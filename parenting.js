"use strict";
/* A framework for parent/child objects */
function ParentingObject() {
	
	var _children = new Array();

	this.children = function () {
		return _children;
	}

	this.addChild = function (child) {
		_children.push(child);
	}

}