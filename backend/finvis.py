import os
# web framework
import bottle
# AAA
from beaker.middleware import SessionMiddleware
from cork import Cork
from cork.backends import MongoDBBackend
import settings
import auth
# Various bits of the app
from mongo import *
import downloader
import crud
import bson

rootdir = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..')

aaa = Cork(backend=MongoDBBackend(db_name='finvis-auth'),
           email_sender=settings.email_sender,
           smtp_url=settings.smtp_url)

app = bottle.app()
session_opts = {
    'session.type': 'cookie',
    'session.validate_key': True,
    'session.cookie_expires': True,
    'session.timeout': 3600 * 24,  # 1 day
    'session.encrypt_key': settings.session_encrypt_key
}
app = SessionMiddleware(app, session_opts)


@bottle.route('/index.html/:entity_id')
@bottle.view('vis')
def vis(entity_id=None):
    if aaa.user_is_anonymous:
        username = None
        admin = False
    else:
        username = aaa.current_user.username
        admin = (aaa.current_user.role == 'admin')

    public_entities = Entity.objects(public=True).only("name")

    if username:
        user_entities = Entity.objects(username=username,
                                       public=False).only('name')
    else:
        user_entities = []

    if entity_id is None:
        redirect('/index.html')

    result = {'username': username,
              'admin': admin,
              'public_entities': public_entities,
              'user_entities': user_entities,
              'initial_id': entity_id,
              'precached_data': precache_entity(entity_id)
              }
    #print(result)
    return result


@bottle.route('/')
@bottle.route('/index.html')
@bottle.route('/s/:state_id')
@bottle.view('vis')
def vis(state_id=None):
    if aaa.user_is_anonymous:
        username = None
        admin = False
    else:
        username = aaa.current_user.username
        admin = (aaa.current_user.role == 'admin')

    public_entities = Entity.objects(public=True).only("name")

    if username:
        user_entities = Entity.objects(username=username,
                                       public=False).only('name')
    else:
        user_entities = []

    if state_id is None:
        state_id = settings.default_initial_state

    result = {'username': username,
              'admin': admin,
              'public_entities': public_entities,
              'user_entities': user_entities,
              'initial_state': state_id,
              'precached_data': precache_state(state_id)
              }
    #print(result)
    return result

def precache_state(state_id):
    """
    Build an array of URLs for scripts containing the requested data as JSONP.
    This lets the data be loaded immediately, rather than having to wait for
    document.ready and the latency associated with another AJAX call.
    """
    (status, result) = crud.state_raw(state_id)
    precached_data = []
    if status == 200:
        precached_data.append("/state.jsonp/" + state_id)
        for child in result.to_mongo()['children']:
            # We're assuming here that any entity in a state is valid
            # Not sure if this is always necessarily true...
            precached_data.append("/entity.jsonp/" + str(child['entityId']))

    return precached_data

def precache_entity(entity_id):
    # TODO: If the id is not found, what is expected to be a JSONP response is
    # instead sent through as plain JSON. This does nothing, and isn't harmful,
    # but it could probably be handled a bit more gracefully...
    precached_data = [ "/entity.jsonp/" + entity_id ]
    return precached_data

# Static files
@bottle.route('/static/<filename:path>')
@bottle.route('/js/<filename:path>')
@bottle.route('/css/<filename:path>')
def static(filename):
    # todo move static assets to static.finvis or somesuch
    # served directly out of nginx for speed
    return bottle.static_file(filename, root=rootdir)


@bottle.route('/images/<filename:path>')
def images(filename):
    return bottle.static_file(filename, root=os.path.join(rootdir, 'images'))


# #  Web application main  # #

def main():

    # Start the Bottle webapp
    #bottle.debug(True)
    bottle.run(app=app, server=bottle.CherryPyServer)

if __name__ == "__main__":
    main()
