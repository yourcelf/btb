/**
	SmartTextBox jQuery plugin
	@version 1.2.0-rc1
	@author Pierre Gayvallet
	@see http://wayofspark.com/projects/smarttextbox
	@copyright (c) 2009-2010 Pierre Gayvallet - GPL license.
*/

(function($){

$.SmartTextBox = {};
var SmartTextBox = $.SmartTextBox;

/**
	SmartTextBox.BaseClass
	Allow pseudo inheritance in javascript objects
*/
SmartTextBox.BaseClass = function(o){};
SmartTextBox.BaseClass.prototype.construct = function(){};
SmartTextBox.BaseClass.extend = function(def) {
  var classDef = function() {
      if (arguments[0] !== SmartTextBox.BaseClass) { this.construct.apply(this, arguments); }
  };
  var proto = new this(SmartTextBox.BaseClass);
  var superClass = this.prototype;
  for(var n in def) {
      var item = def[n];
      proto[n] = item;
  }
  classDef.prototype = proto;
  classDef.extend = this.extend;      
  return classDef;
};

/**
	SmartTextBox.SmartTextBox
	Manager Class for a TextBox
*/
SmartTextBox.SmartTextBox = SmartTextBox.BaseClass.extend({
	_options : {
		// Autocomplete configuration
		autocomplete : true,  	 			// on/off
		minSearchLength : 2,       			// min length to type to receive suggestions
		maxResults : 10,     			    // max number of results to display
		caseSensitive : false,  		    // case sensitive search
		highlight : true,				    // highlight autocomplete search in results
		fullSearch : true,                  // search at start of values or in all the string
		autocompleteValues : [],
        autocompleteUrl : null,
		placeholder : "Please start typing to receive suggestions", // search placeholder text
		// SmartTextBox configuration
		onlyAutocomplete: false,            // can only insert from autocomplete values
        uniqueValues : true,                // values can only be added once  
		submitKeys : [13],					// list of keys to save an input to box
		submitChars : [ ";", ","],			// list of chars to save an input to box
		separator : ";",					// separator for serialize method
		updateOriginal : true,				// update the original input value when change
		// Events handling
		onElementAdd : 		null,
		onElementRemove : 	null,
		onElementFocus : 	null,
		onElementBlur : 	null,
		// Misc
		hideEmptyInputs : true,               // hide empty inputs
        editOnFocus : false,                  // edit box on focus ( click or <- -> )
        editOnDoubleClick : false,            // edit box on doubleClick
		// CSS
		containerClass : "smartTextBox",  // base CSS class for containers
		// Debug configuration
		debug : false						// debug mode - show logs in firebug console
	},
	construct : function(el, o){
		this.options = {};
		var o = o || {};
		$.extend(this.options, this._options);
		$.extend(this.options, o);
		
		var self = this;
		this.original = $(el);
		this.focused = false;
		this.elements = [];
		
		$(this.original).data("SmartTextBox", this);
		this.original.hide();
		
		this.container = $("<div></div>")
			.addClass(this.options.containerClass)
			 .click(function(e){
				if( (self.container.index(e.target)>-1 || self.list.index(e.target)>-1) &&
					(!self.currentFocus || self.currentFocus != self.elements[self.elements.length-1]))
						self.focusLast();												
			 }).insertAfter(this.original);
										 
		this.list = $("<ul></ul>")
			.addClass(this.options.containerClass + "-items")
			.appendTo(this.container);
								  
		$(document).keydown(function(e){
						self.onKeyDown(e)
					})
				   .click(function(e){
						if(!self.currentFocus) return;
						if (e.target.className.indexOf(self.options.containerClass)>-1){
							if(self.container.index(e.target)>-1) return;
							var parent = $(e.target).parents('.' + self.options.containerClass);
							if (parent.index(self.container)>-1) return;
						}
						self.blur();
					});
		
		if(this.options.autocomplete){
			this.autocomplete = new SmartTextBox.AutoComplete(this, this.options);
		}
		
		this.add("input");
		this.loadOriginal();
	},
	setValues : function(values){
		this.removeAll();
		var self = this;
		$.each(values, function(i, el){
			self.addBox(el);
		});
	},
	removeAll : function() {
		var toRemove = [];
		$.each(this.elements, function(){
			if(this.is('box')) {
				toRemove.push(this);
			}
		})
		$.each(toRemove, function(){
			this.remove();
		})
	},
	setAutocompleteValues : function(values){
		if(!this.options.autocomplete) return;
		if(typeof values == "string") {
			this.autocomplete.setValues(values.split(this.options.separator));
		} else {
			this.autocomplete.setValues(values);
		}
	},
	onKeyDown : function(event){
		if(!this.currentFocus) return;
		
		var caret = this.currentFocus.is('input') ? this.currentFocus.getCaret() : null;
		var value = this.currentFocus.getValue();
		var custom = (this.currentFocus.is('input') && this.currentFocus.isSelected());
		
		// bug on FF making elem to loose focus... this fix it
		this.currentFocus.valueContainer.focus();
		
		switch(event.keyCode){
			case 37: // <-
				if( this.currentFocus.is('box') || ((caret == 0 || !value.length) && !custom) ){
					event.preventDefault();
					this.focusRelative('previous');
				}
				break;
			case 39: // ->
				if( this.currentFocus.is('box') || (caret == value.length && !custom)){
					event.preventDefault();
					this.focusRelative('next');
				}
				break;
			case 8: // backspace
				if(this.currentFocus.is('box')){
					this.currentFocus.remove();
					event.preventDefault();
				} else if ((caret == 0 || !value.length) && !custom) {
					this.focusRelative('previous');
					event.preventDefault();
				}		
				break;
			case 27: // escape
				this.blur();
				break;
		}
	},
	create : function(type, value, options){
		var n;
		if(type=="box"){
			n = new SmartTextBox.BoxElement(value, this, options);
		}
		else if(type=="input"){
			n = new SmartTextBox.InputElement(value, this, options);
		}
		else{
			// handle case - do nothing for now.
		}
		return n;
	},
	getElementIndex : function(elem){
		return $(this.elements).index(elem);
	},
	getElement : function(index){
		if((index<0) || (index>this.elements.length-1)) return null;
		return this.elements[index];
	},
	getElementsByType : function(type) {
		var els = [];
		$.each(this.elements, function(){
			if(this.is(type)) {
				els.push(this);
			}
		});
		return els;
	},
	getLastBox : function(){
		for(var i=this.elements.length-1;i>-1;i--){
			if(this.elements[i].is('box')) return this.elements[i];
		}
		return null;
	},
	insertElement : function(element, index){
		var i = (arguments.length > 1) ? index : this.elements.length;
		this.elements.splice(i,0, element);
	},
	add : function(type, value, relTo, relPos){
		var type = type || "box";
		var value = value || "";
		var relPos = relPos || "after"
		var relTo = relTo || this.getLastBox();
		
		var n = this.create(type, value);
		var i = 0;
		if(relTo) i = this.getElementIndex(relTo) + ((relPos=='after') ? 1 : 0);

		this.insertElement(n, i);
		relTo ? n.inject(relTo, relPos) : n.inject();
		return n;
	},
	addBox : function(value, relTo, relPos){
		if(!$.trim(value).length) return;
		return this.add("box", $.trim(value), relTo, relPos);
	},
	removeBox : function(valueOrIndex) {
		var found = null;
		$.each(this.elements, function(){
			if(this.getValue()==valueOrIndex) {
				found = this;
				return false;
			}
		});
		if(!found&&!isNaN(valueOrIndex)) {
			var boxes = this.getElementsByType("box");
			if(boxes.length>valueOrIndex) {
				found = boxes[valueOrIndex];
			}
		}
		if(found) {
			found.remove();
		}
	},
	handleElementEvent : function(type, elem, options){
		switch(type){
			case "add":
				this.onElementAdd(elem, options);
				break;
			case "focus":
				this.onElementFocus(elem, options);
				break;
			case "blur" :
				this.onElementBlur(elem, options);
				break;
			case "remove" :
				this.onElementRemove(elem, options);
				break;
		}
	},
	onElementAdd : function(elem){
		if(this.autocomplete) this.autocomplete.setupElement(elem);
		if(elem.is('box')){
			var i = this.getElementIndex(elem);
			var prev = this.getElement(i-1);
			if((prev && prev.is('box')) || (!prev)){
				var b = this.add("input", "", elem, "before");
				if(this.options.hideEmptyInputs) b.hide();
			}
			if(this.options.updateOriginal) this.updateOriginal();
			if(this.options.onElementAdd) this.options.onElementAdd(elem, this);
		}
	},
	onElementFocus : function(elem){
		if(this.currentFocus==elem) return;
		if(this.currentFocus) this.currentFocus.blur();
		this.currentFocus = elem;
		if(this.currentFocus.is('input')&&this.autocomplete) this.autocomplete.search(this.currentFocus);
		if(this.options.onElementFocus) this.options.onElementFocus(elem, this);
	},
	onElementBlur : function(elem){
		if(this.currentFocus==elem){
			this.currentFocus = null;
			if(this.autocomplete) this.autocomplete.hide();
			if(this.options.onElementBlur) this.options.onElementBlur(elem, this);
		}
	},
	onElementRemove : function(elem){
		var removedIndex = this.getElementIndex(elem);
		this.focusRelative((removedIndex==this.elements.length-1) ? 'previous' : 'next', elem);
		this.elements.splice(removedIndex, 1);
		if(this.getElement(removedIndex)&&this.getElement(removedIndex).is("input")) {
			if((this.getElement(removedIndex+1)&&this.getElement(removedIndex+1).is("input"))||
			   (this.getElement(removedIndex-1)&&this.getElement(removedIndex-1).is("input"))) {
				this.getElement(removedIndex).remove();
			}
		}
		if(this.options.updateOriginal) this.updateOriginal();
		if(this.elements.length==1&&this.elements[0].is("input")) {
			this.elements[0].show();
		}
		if(this.options.onElementRemove) this.options.onElementRemove(elem, this);
	},
	blur: function(){
		$.each(this.elements, function(i, el){
			el.blur();
		});
	},
	focusLast : function(){
		this.elements[this.elements.length-1].focus();
	},
	focusRelative : function(dir, from){
		var b = from || this.currentFocus;
		var idx = $(this.elements).index(b);
		idx = (dir == 'previous') ? idx-1 : idx+1;
		if(idx<0) return; //idx = 0;
		if(idx>=this.elements.length) return; //idx = this.elements.length-1;
		this.elements[idx].focus();
		if(this.elements[idx].is("input")){
			(dir == 'previous') ? this.elements[idx].setCaretToEnd() : this.elements[idx].setCaretToStart();
		}
	},
	getBoxValues : function() {
        var values = [];
		$.each(this.elements, function(i, el){
            if(!this.is('box')) return;
            values.push(this.getValue());
        });
		return values;
	},
	containsValue : function(value) {
		return ($(this.getBoxValues()).index(value)>-1);
	},
	serialize : function(){
		return this.getBoxValues().join(this.options.separator);
	},
	updateOriginal : function(){
		this.original.attr('value', this.serialize());
	},
	loadOriginal : function(){
		this.load(this.original.attr('value'));
	},
	load : function(values){
		if(typeof values == "string") {
			var values = values.split(this.options.separator);
		} 
		this.setValues(values);
	}
});

/** 
	SmartTextBox.AutoComplete
*/
SmartTextBox.AutoComplete = SmartTextBox.BaseClass.extend({
	_options : {
	},
	construct : function(stb, o){
		this.stb = stb;
		this.currentValue = "";
		this.options = {};
		$.extend(this.options, this._options);
		$.extend(this.options, o || {});
		if (this.options.autocompleteUrl) {
			this.ajaxLoad(this.options.autocompleteUrl);
		} else {
			this.setValues(this.options.autocompleteValues);
		}
		var self = this;
		this.baseClass = this.stb.options.containerClass + "-autocomplete";
		
		this.container = $("<div></div>")
							.addClass(this.baseClass)
							.css("width", this.stb.container.width())
							.appendTo(this.stb.container);
		this.placeHolder = $("<div></div>")
								.addClass(this.baseClass + "-placeholder")
								.html(this.options.placeholder)
								.appendTo(this.container)
								.hide();
		this.resultList = $("<div></div>")
								.addClass(this.baseClass + "-results")
								.appendTo(this.container)
								.hide();
	},
	ajaxLoad : function(url) {
	   var self = this;
	   $.get(url, {}, function(response){
	       var values = response.values;
		   self.setValues(values);
	   }, 'json');
	},
	setValues : function(values){
		this.values = values || [];
	},
	getValues : function(){
		return this.values || [];
	},
	setupElement : function(element){
		if(!element.is('input')) return;
		var self = this;
		element.valueContainer
					.keydown(function(e){ self.navigate(e);  })
					.keyup(function(){ self.search(); });
	},
	navigate : function(e){
		switch(e.keyCode){
			case 38: // arrowUp
				(this.currentSelection && this.currentSelection.prev().length) ? this.focusRelative('prev') : this.blur(); 
				break;
			case 40: // arrowDown
				this.currentSelection ? this.focusRelative('next') : this.focusFirst();
				break;
			case 13: // enter
				if(this.currentSelection){
					e.stopPropagation();
					this.addCurrent();
					this.currentElem.focus();
					this.search();
				}
				break;
		};
	},
	search : function(elem){		
		if(elem) this.currentElem = elem;
		if (!this.getValues().length) return;
		window.clearTimeout(this.hidetimer);
		var value = this.currentElem.getValue();
		if(value.length<this.options.minSearchLength) this.showPlaceHolder();
		if (value == this.currentValue) return;
		this.currentValue = value;
		this.hideResultList();
		if(value.length<this.options.minSearchLength) return;
		this.showResults(value);
	},
	showPlaceHolder : function(){
		if(this.placeHolder) this.placeHolder.show();
	},
	hidePlaceHolder : function(){
		if(this.placeHolder) this.placeHolder.hide();
	},
	showResultList : function(){
		this.resultList.show();
	},
	hideResultList : function(){
		this.resultList.hide();
	},
	hide : function(){
		var self = this;
		this.hidetimer = window.setTimeout(function(){
			self.hidePlaceHolder();
			self.hideResultList();
			self.currentValue = "";
		}, 150);
	},
	showResults : function(value){
		var results = this.searchResults(value);
		this.hidePlaceHolder();
		if(!results.length) return;
		this.blur();
		this.resultList.empty().show();
		var self = this;
		results.sort();
		$.each(results, function(i, e){
			self.addResult(e, value);
		});
		this.results = results;
	},
	searchResults : function(value){
		var newvals = [], regexp = new RegExp((this.options.fullSearch ? '' : '\\b') + value, this.caseSensitive ? '' : 'i');
		var values = this.getValues(); 
		for (var i = 0; i < values.length; i++){
			if(this.stb.options.uniqueValues&&this.stb.containsValue(values[i])) continue;
			if (regexp.test(values[i])) {
				newvals.push(values[i]);
			}
			if (newvals.length >= this.options.maxResults) break;
		}
		return newvals;
	},
	addResult : function(result, value){
		var self = this;
		var newSel = $("<div></div>")
		   .addClass(this.baseClass+"-result")
		   .appendTo(this.resultList)
		   .mouseenter(function(e){
				self.focus(this);
		   })
		   .mousedown(function(e){
				e.stopPropagation();
				window.clearTimeout(self.hidetimer);
				self.doAdd = true;
		   })
		   .mouseup(function(e){
				if(self.doAdd){
					self.addCurrent();
					self.currentElem.focus();
					self.search();
					self.doAdd = false;
				}
		   });
		   
        var valueContainer = $("<span>")
		    .addClass(self.baseClass+"-value")
            .html(result)
			.css("display", "none")
			.appendTo(newSel);
	    var displayContainer = $("<span>")
	       .addClass(self.baseClass+"-display")
		   .html(self.formatResult(result, value))
		   .appendTo(newSel);			  
	},
	formatResult : function(result, value) {
		if (this.options.highlight) {
			var lcr = result.toLowerCase();
			var lcv = value.toLowerCase();
			var idx = lcr.indexOf(lcv);
			var formatted = "<span>" + result.substring(0, idx) + "</span>" +
			                "<span class='" + this.baseClass + "-highligh'>" + result.substring(idx, idx + value.length) + "</span>" + 
							"<span>" + result.substring(idx + value.length) + "</span>";
			return formatted;
		} else {
			return result;
		}
	},
	addCurrent : function(){
		var value = $("."+this.baseClass+"-value", this.currentSelection).html(); 
		this.currentElem.setValue(value);
		this.currentElem.saveAsBox();
		this.currentSelection = null;
	},
	focus : function(element){
		this.blur();
		this.currentSelection = $(element).addClass(this.baseClass + '-result-focus');
	},
	focusFirst : function(){
		this.focus(this.resultList.children(":first"));
	},
	focusRelative : function(dir){
		if(dir=='next'){
			this.focus( this.currentSelection.next().length ? this.currentSelection.next() : this.currentSelection);
		}
		else{
			this.focus( this.currentSelection.prev().length ? this.currentSelection.prev() : this.currentSelection);
		}
	},
	blur : function(){
		if(this.currentSelection){
			this.currentSelection.removeClass(this.baseClass + "-result-focus");
			this.currentSelection = null;
		}
	}
});


/**
	SmartTextBox.GrowingInput
*/
SmartTextBox.GrowingInput = SmartTextBox.BaseClass.extend({	
	options: {
		min: 0,
		max: null,
		startWidth: 2,
		correction: 10
	},
	construct : function(el, o){
		var o = o || {}; $.extend(this.options, o);
		var self = this;
		this.element = $(el);
		
		this.calc = $("<span></span>")
						.css({
							'float': 'left',
							'display': 'inline-block',
							'position': 'absolute',
							'left': -1000
						})
						.insertAfter(this.element);

		this.requiredStyles = ['font-size', 'font-family', 'padding-left', 'padding-top', 'padding-bottom', 
							   'padding-right', 'border-left', 'border-right', 'border-top', 'border-bottom', 
							   'word-spacing', 'letter-spacing', 'text-indent', 'text-transform'];
		
		this.copyCat();			
		this.resize();
		var resize = function(){ self.resize(); }
		this.element.click(resize)
					.blur(resize)
					.keyup(resize)
					.keydown(resize)
					.keypress(resize);
	},
	copyCat : function(){
		var self = this;
		$.each(this.requiredStyles, function(i, el){
			self.calc.css(el, self.element.css(el));
		});
	},
	calculate: function(chars){
		this.calc.html(chars);
		var width = this.calc.width();
		return (width ? width : this.options.startWidth) + this.options.correction;
	},
	resize: function(){
		this.lastvalue = this.value;
		this.value = this.element.attr('value');
		var value = this.value;
		
		if((this.options.min || (this.options.min==0)) && this.value.length < this.options.min){
			if((this.lastvalue || (this.lastvalue==0)) && (this.lastvalue.length <= this.options.min)) return;
			for(var i=0; i<this.options.min; i++){ value += "-";}
		}
		if((this.options.max || (this.options.max==0)) && this.value.length > this.options.max){
			if((this.lastvalue || (this.lastvalue==0)) && (this.lastvalue.length >= this.options.max)) return;
			value = this.value.substr(0, this.options.max);
		}
		
		var newWidth = this.calculate(value);
		this.element.width(newWidth);
		return this;
	}
});

/**
 * SmartTextBox.BaseElement - Base, abstract class for SmartTextBox elements
 */
SmartTextBox.BaseElement = SmartTextBox.BaseClass.extend({
	type : "base",
	options : {
	},
	construct : function(value, stb, o){
		var o = o || {}; $.extend(this.options, o);
		this.value = value;
		this.stb = stb;
		this.className = this.stb.options.containerClass + "-elem";
		this.elemClassName = this.stb.options.containerClass + "-" + this.type +"-elem";
		this.focused = false;
		this.init();
	},
	init : function(){
		this.constructElement();
	},
	constructElement : function(){
		this.el = null;
	},
	is : function(t){
		return this.type==t;
	},
	inject : function(elem, pos){
		if(elem) (pos == 'before') ? this.getElement().insertBefore(elem.getElement()) : this.getElement().insertAfter(elem.getElement());
		else this.getElement().prependTo(this.stb.list);
		this.notifyEvent("add");
	},
	remove : function(notify){
		this.blur();
		this.el.remove();
		this.onRemove();
		var n = (typeof notify == 'undefined') ? true : notify;
		if(n) this.notifyEvent("remove");
	},
	focus : function(notify){
		if(this.focused) return this;
		this.show();
		this.el.addClass(this.className + "-focus")
			   .addClass(this.className + "-" + this.type + "-focus");
		this.focused = true;
		
		var n = (typeof notify == 'undefined') ? true : notify;
		if(n) this.notifyEvent('focus');
		this.onFocus();
		
		return this;
	},
	blur : function(notify){
		if(!this.focused) return this;
		this.el.removeClass(this.className + "-focus")
			   .removeClass(this.className + "-" + this.type + "-focus");
		this.focused = false;
		
		var n = (typeof notify == 'undefined') ? true : notify;
		if(n) this.notifyEvent('blur');
		this.onBlur();
		
		return this;
	},
	onMouseIn : function(){
		this.el.addClass(this.className + "-hover")
			   .addClass(this.className + "-" + this.type + "-hover");
	},
	onMouseOut : function(){
		this.el.removeClass(this.className + "-hover")
			   .removeClass(this.className + "-" + this.type + "-hover");
	},
	onFocus : function(){
		return;
	},
	onBlur : function(){
		return;
	},
	onRemove : function(){
		return;
	},
	show : function(notify){
		this.el.show();
		var n = (typeof notify == 'undefined') ? true : notify;
		if(n) this.notifyEvent('show');
		return this;
	},
	hide : function(notify){
		this.el.hide();
		var n = (typeof notify == 'undefined') ? true : notify;
		if(n) this.notifyEvent('hide');
		return this;
	},
	setValue : function(v, notify){
		this.value = v;
		this.valueContainer.text(v);
		var n = (typeof notify == 'undefined') ? true : notify;
		if(n) this.notifyEvent("setValue");
		return this;
	},
	getValue : function(){
		return this.value;
	},
	getElement : function(){
		return this.el;
	},
	notifyEvent : function(type){
		this.stb.handleElementEvent(type, this);
		return this;
	},
	toString : function(){
		return "[BoxElement type='" + this.type + "' value='" + this.getValue() + "']";
	}
});

/**
	SmartTextBox.BoxElement
*/
SmartTextBox.BoxElement = SmartTextBox.BaseElement.extend({
	type : "box",
	constructElement : function(){
		var self = this;
		this.el = $("<li></li>")
			.addClass(this.className)
			.addClass(this.elemClassName)
			.hover(
				function(){ self.onMouseIn();  },
				function(){ self.onMouseOut(); }
			)
			.mousedown(function(event){
				self.focus();
			});

		if(this.stb.options.editOnDoubleClick){
			this.el.dblclick(function(event){
				event.preventDefault();
				self.toInput();
			});
		}
		
		this.valueContainer = $("<span></span>")
			.addClass(this.className+"-valueContainer")
			.appendTo(this.el);
		
		this.removeButton = $("<a></a>")
			.addClass(this.className+"-deleteButton")
			.attr("href", "javascript:;")
			.click(function(e){ self.remove(); e.stopPropagation(); })
			.appendTo(this.el);
			
		this.setValue(this.value);
	},
	onFocus : function(){
		var self = this;
		if(this.stb.options.editOnFocus){
			window.setTimeout(function(){
				self.toInput()
			}, 50);
		}
	},
	onBlur : function(){
		return;
	},
	toInput : function(){
		var v = this.getValue();
		var idx = this.stb.getElementIndex(this);
		this.remove();
		var nextElem = this.stb.getElement(idx-1);
		if(nextElem.is("input") && !$.trim(nextElem.getValue()).length){
			nextElem.setValue(v);
			nextElem.valueContainer.focus();
			nextElem.setCaretToEnd();
		}
	}
});

/**
	SmartTextBox.InputElement
*/
SmartTextBox.InputElement = SmartTextBox.BaseElement.extend({
	type : "input",
	constructElement : function(){
		var self = this;
		this.el = $("<li></li>")
			.addClass(this.className)
			.addClass(this.elemClassName)
			.hover(
				function(){ self.onMouseIn(); },
				function(){ self.onMouseOut(); }
			)
			.click(
				function(){ self.focus(); }
			);
					
		this.valueContainer = $("<input />")
			.addClass(this.elemClassName+"-valueInput")
			.focus( function(event){ event.stopPropagation(); self.focus(); })
			.blur( function(event){ self.blur(); })
			.appendTo(this.el);
		
		this.growingInput = new SmartTextBox.GrowingInput(this.valueContainer);

		$(document).keydown( function(event){ self.onKeyDown(event) } );
		$(document).keypress( function(event){ self.onKeyPress(event) } );
		
		this.setValue(this.value);
	},
	getValue : function(){
		return this.valueContainer.attr('value');
	},
	setValue : function(v){
		this.value = v;
		this.valueContainer.attr("value", v);
		this.growingInput.resize();
		this.notifyEvent("setValue");
		return this;
	},
	getCaret: function(){
		var elem = this.valueContainer[0];
		if(elem.createTextRange) {
			var r = document.selection.createRange().duplicate();		
			r.moveEnd('character', elem.value.length);
			if (r.text === '') return elem.value.length;
			return elem.value.lastIndexOf(r.text);
		} else {
			return elem.selectionStart;
		}
	},
	getCaretEnd: function(){
		var elem = this.valueContainer[0];
		if (elem.createTextRange){
			var r = document.selection.createRange().duplicate();
			r.moveStart('character', -elem.value.length);
			return r.text.length;
		} else {
			return elem.selectionEnd;
		}
	},
	setCaret: function(pos){
		var elem = this.valueContainer[0];
		if(elem.createTextRange){
			elem.focus ();
			var sel = document.selection.createRange();
			sel.moveStart('character', -elem.value.length);
			sel.moveStart('character', pos);
			sel.moveEnd('character', 0);
			sel.select();
		}
		else{
			elem.selectionStart = pos; 
			elem.selectionEnd = pos;
		}
	},
	setCaretToStart : function(){
		this.setCaret(0);
	},
	setCaretToEnd : function(){
		this.setCaret(this.valueContainer.attr("value").length || 0);
	},
	isSelected: function(){
		return this.focused && (this.getCaret() !== this.getCaretEnd());
	},
	saveAsBox : function(){
		var v = this.getValue();
		if(!v) return;
		this.stb.add("box", $.trim(v), this, "before");
		this.setValue("");
	},
	onKeyDown : function(event){
		if(!this.focused) return;
		if($.inArray(event.keyCode, this.stb.options.submitKeys)>-1 &&
		   !this.stb.options.onlyAutocomplete &&
		   !(this.stb.options.uniqueValues&&this.stb.containsValue(this.getValue()))) {
			event.preventDefault();
			this.saveAsBox();
		}
	},
	onKeyPress : function(event){
		if(!this.focused) return;
		if($.inArray(String.fromCharCode(event.charCode || event.keyCode || 0), this.stb.options.submitChars)>-1 &&
		   !this.stb.options.onlyAutocomplete && 
		   !(this.stb.options.uniqueValues&&this.stb.containsValue(this.getValue()))) {
			event.preventDefault();
			this.saveAsBox();
		}
	},
	onFocus : function(){
		this.show();
		this.valueContainer.focus();
		this.growingInput.resize();
	},
	onBlur : function(){
		this.valueContainer.blur();
		if(this.stb.options.hideEmptyInputs && this.el.next().length && !this.getValue()) this.hide();
		if(this.stb.options.editOnFocus){
			this.saveAsBox();
		}
	}
});

// Adds SmartTextBox to jQuery fn functions
$.fn.extend({
	smartTextBox: function(key, value){
		return this.each(function(){
			var Smb = $(this).data("SmartTextBox");
			if(Smb) {
				switch(key){
					case "add":
						Smb.addBox(value);
						break;
					case "remove":
						Smb.removeBox(value);
						break;
					case "load":
						Smb.load(value);
						break;
					case "clear":
						Smb.removeAll();
						break;
					case "autocomplete":
						Smb.setAutocompleteValues(value);
						break;
				}
			} else {
				new $.SmartTextBox.SmartTextBox(this, key);
			}
		});
	}
});

})(jQuery);
