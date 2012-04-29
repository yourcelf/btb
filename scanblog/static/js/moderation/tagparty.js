(function() {
  var __hasProp = Object.prototype.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor; child.__super__ = parent.prototype; return child; },
    __bind = function(fn, me){ return function(){ return fn.apply(me, arguments); }; };

  if (window.btb == null) window.btb = {};

  btb.Tag = (function(_super) {

    __extends(Tag, _super);

    function Tag() {
      Tag.__super__.constructor.apply(this, arguments);
    }

    return Tag;

  })(Backbone.Model);

  btb.TagList = (function(_super) {

    __extends(TagList, _super);

    function TagList() {
      TagList.__super__.constructor.apply(this, arguments);
    }

    TagList.prototype.url = "/moderation/tagparty/tags/";

    TagList.prototype.model = btb.Tag;

    return TagList;

  })(Backbone.Collection);

  btb.TagForm = (function(_super) {

    __extends(TagForm, _super);

    function TagForm() {
      this.addTag = __bind(this.addTag, this);
      this.saveTags = __bind(this.saveTags, this);
      this.render = __bind(this.render, this);
      this.rechoose = __bind(this.rechoose, this);
      this.fetchDocument = __bind(this.fetchDocument, this);
      TagForm.__super__.constructor.apply(this, arguments);
    }

    TagForm.prototype.template = _.template($("#tagpanelTemplate").html() || "");

    TagForm.prototype.events = {
      "submit form.tagparty": "saveTags",
      "click a.tag": "addTag",
      "change form.tagparty select": "rechoose"
    };

    TagForm.prototype.initialize = function(options) {
      this.possible = new btb.TagList();
      this.possible.reset(options.tags);
      console.log(this.possible);
      this.chosen = [];
      return this.fetchDocument();
    };

    TagForm.prototype.fetchDocument = function() {
      var _this = this;
      return $.ajax({
        url: "/moderation/tagparty/next/",
        type: "get",
        success: function(data) {
          var doc, li;
          doc = $("<div>" + data + "</div>");
          $("#doc").html(doc.find(".post-detail").html());
          _this.chosen = (function() {
            var _i, _len, _ref, _results;
            _ref = doc.find("ul.tags li");
            _results = [];
            for (_i = 0, _len = _ref.length; _i < _len; _i++) {
              li = _ref[_i];
              _results.push($.trim($(li).text()));
            }
            return _results;
          })();
          _this.tagURL = doc.find(".tagform form").attr("action");
          return _this.render();
        },
        error: function(xhr, statusText, error) {
          switch (xhr.status) {
            case 404:
              return alert("No more untagged posts!");
            default:
              return alert("Server error!");
          }
        }
      });
    };

    TagForm.prototype.rechoose = function() {
      this.chosen = this.$("select", "form.tagparty").val() || [];
      return this.render();
    };

    TagForm.prototype.render = function() {
      var possible, tag, _i, _len, _ref;
      $("#tagpanel").html(this.el);
      possible = [];
      _ref = this.possible.models;
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        tag = _ref[_i];
        if (!_.contains(this.chosen, tag.get("name"))) {
          possible.push({
            name: tag.get("name"),
            chosen: false
          });
        }
      }
      this.$el.html(this.template({
        possible: possible,
        chosen: this.chosen
      }));
      this.$(".chosen-tags").tagit({
        tagSource: _.map(possible, function(a) {
          return a.name;
        }),
        triggerKeys: ['enter', 'comma', 'tab'],
        allowNewTags: false,
        select: true
      });
      return this.delegateEvents();
    };

    TagForm.prototype.saveTags = function(event) {
      var tags,
        _this = this;
      $(event.currentTarget).addClass("loading");
      tags = (this.$("select", "form.tagparty").val() || []).join(",");
      $.ajax({
        url: this.tagURL,
        success: function() {
          $(event.currentTarget).removeClass("loading");
          return _this.$(".status").addClass("success").html("All good!");
        },
        error: function() {
          alert("Server error");
          $(event.currentTarget).removeClass("loading");
          return _this.$(".status").addClass("warn").html("Oh no!");
        },
        type: "POST",
        data: {
          tags: tags
        }
      });
      return false;
    };

    TagForm.prototype.addTag = function(event) {
      this.chosen.push($.trim($(event.currentTarget).text()));
      this.render();
      return false;
    };

    return TagForm;

  })(Backbone.View);

}).call(this);
