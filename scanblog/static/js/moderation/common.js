(function() {
  var btb,
    __slice = Array.prototype.slice,
    __bind = function(fn, me){ return function(){ return fn.apply(me, arguments); }; },
    __hasProp = Object.prototype.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor; child.__super__ = parent.prototype; return child; };

  if (window.btb == null) window.btb = {};

  btb = window.btb;

  btb.strToDate = function(dateOrStr) {
    var part, parts;
    if (_.isString(dateOrStr)) {
      parts = [
        (function() {
          var _i, _len, _ref, _results;
          _ref = dateOrStr.split(/[^0-9]+/g);
          _results = [];
          for (_i = 0, _len = _ref.length; _i < _len; _i++) {
            part = _ref[_i];
            _results.push(parseInt(part, 10));
          }
          return _results;
        })()
      ][0];
      return new Date(parts[0], parts[1] - 1, parts[2], parts[3], parts[4], parts[5]);
    }
    return dateOrStr;
  };

  btb.formatDate = function(dateOrStr) {
    var d;
    d = btb.strToDate(dateOrStr);
    return d.getFullYear() + "-" + (1 + d.getMonth()) + "-" + d.getDate();
  };

  btb.formatDateTime = function(dateOrStr) {
    var d;
    d = btb.strToDate();
    return btb.formatDate(d) + " " + d.getHours() + ":" + d.getMinutes();
  };

  btb.dateInterval = function(d1, d2) {
    var interval;
    interval = Math.abs(btb.strToDate(d1).getTime() - btb.strToDate(d2).getTime());
    return interval / 1000;
  };

  btb.englishDateInterval = function(d1, d2) {
    var i, interval, word;
    interval = btb.dateInterval(d1, d2);
    if (interval < 60) {
      i = parseInt(interval);
      word = "second";
    } else if (interval < 60 * 60) {
      i = parseInt(interval / 60);
      word = "minute";
    } else if (interval < 60 * 60 * 24) {
      i = parseInt(interval / 60 / 60);
      word = "hour";
    } else {
      i = parseInt(interval / 60 / 60 / 24);
      word = "day";
    }
    return ("" + i + " " + word) + (i !== 1 ? "s" : "");
  };

  btb.ellipsisWithMore = function(str, length) {
    if (length == null) length = 200;
    if (str.length < length) return str;
    return ("<span>" + (str.substr(0, 200)) + "</span>\n") + ("<span style='display: none;'>" + (str.substr(200)) + "</span>\n") + "<span class='link-like' onclick='$(this).prev().show(); $(this).hide();'>...</span>";
  };

  btb.zeroPad = function(num, digits) {
    num = "" + num;
    while (num.length < digits) {
      num = "0" + num;
    }
    return num;
  };

  btb.colorStripes = function() {
    var colors, compats, func, i, oldWebkitArgs, oldWebkitStops, percent, selector, standardArgs, standardStops, _i, _len, _ref, _results;
    selector = arguments[0], colors = 2 <= arguments.length ? __slice.call(arguments, 1) : [];
    percent = 100.0 / colors.length;
    standardStops = [];
    oldWebkitStops = [];
    for (i = 0, _ref = colors.length; 0 <= _ref ? i < _ref : i > _ref; 0 <= _ref ? i++ : i--) {
      standardStops.push("" + colors[i] + " " + (percent * i) + "%, " + colors[i] + " " + (percent * (i + 1)) + "%");
      oldWebkitStops.push("color-stop(" + (percent * i) + "%, " + colors[i] + "), color-stop(" + (percent * (i + 1)) + "%, " + colors[i] + ")");
    }
    standardArgs = "top, " + standardStops.join(", ");
    oldWebkitArgs = "linear, 50% 0%, 50% 100%, " + oldWebkitStops.join(", ");
    $(selector).css("background-image", "-webkit-gradient(" + oldWebkitArgs + ")");
    compats = ["-webkit-linear-gradient", "-moz-linear-gradient", "-o-linear-gradient", "-ms-linear-gradient", "linear-gradient"];
    _results = [];
    for (_i = 0, _len = compats.length; _i < _len; _i++) {
      func = compats[_i];
      _results.push($(selector).css("background-image", "" + func + "(" + standardArgs + ")"));
    }
    return _results;
  };

  btb.transform = function(selector, scale, rotate, translateXY, originXY) {
    var origin, prefix, trans, _i, _len, _ref, _results;
    trans = "scale(" + scale + ", " + scale + ") rotate(" + rotate + ") translate(" + translateXY[0] + ", " + translateXY[1] + ")";
    origin = originXY.join(" ");
    _ref = ["-moz-", "-webkit-", "-o-", "-ms-", ""];
    _results = [];
    for (_i = 0, _len = _ref.length; _i < _len; _i++) {
      prefix = _ref[_i];
      _results.push($(selector).css("" + prefix + "transform", trans).css("" + prefix + "transform-origin", origin));
    }
    return _results;
  };

  btb.FilteredPaginatedCollection = (function(_super) {

    __extends(FilteredPaginatedCollection, _super);

    function FilteredPaginatedCollection() {
      this.fetchById = __bind(this.fetchById, this);
      FilteredPaginatedCollection.__super__.constructor.apply(this, arguments);
    }

    FilteredPaginatedCollection.prototype.pagination = {};

    FilteredPaginatedCollection.prototype.filter = {};

    FilteredPaginatedCollection.prototype.url = function() {
      if (this.filter) {
        return "" + this.baseUrl + "?" + ($.param(this.filter));
      } else {
        return this.baseUrl;
      }
    };

    FilteredPaginatedCollection.prototype.parse = function(response) {
      this.pagination = response.pagination;
      return response.results;
    };

    FilteredPaginatedCollection.prototype.fetchById = function(id, options) {
      this.filter = {
        id: id
      };
      return this.fetch(options);
    };

    return FilteredPaginatedCollection;

  })(Backbone.Collection);

  btb.PaginatedView = (function(_super) {

    __extends(PaginatedView, _super);

    function PaginatedView() {
      this.setPageDoneLoading = __bind(this.setPageDoneLoading, this);
      this.setPageLoading = __bind(this.setPageLoading, this);
      PaginatedView.__super__.constructor.apply(this, arguments);
    }

    PaginatedView.prototype.paginationTemplate = _.template($("#pagination").html() || "");

    PaginatedView.prototype.renderPagination = function(collection, el) {
      var i, links, p, _ref;
      p = collection.pagination;
      links = [];
      for (i = 1, _ref = p.pages; 1 <= _ref ? i <= _ref : i >= _ref; 1 <= _ref ? i++ : i--) {
        if (i < 10 || Math.abs(p.page - i) < 5 || i > p.pages - 10) links.push(i);
      }
      el.html(this.paginationTemplate({
        pagination: p,
        pageLinksToShow: links
      }));
      return this;
    };

    PaginatedView.prototype.newPageFromEvent = function(event) {
      return parseInt($.trim($(event.currentTarget).text()));
    };

    PaginatedView.prototype.setPageLoading = function() {
      return $(".pagination-loading", this.el).show();
    };

    PaginatedView.prototype.setPageDoneLoading = function() {
      return $(".pagination-loading", this.el).hide();
    };

    return PaginatedView;

  })(Backbone.View);

  btb.TabularList = (function(_super) {

    __extends(TabularList, _super);

    function TabularList() {
      this.turnPage = __bind(this.turnPage, this);
      this.render = __bind(this.render, this);
      TabularList.__super__.constructor.apply(this, arguments);
    }

    TabularList.prototype.tagName = 'table';

    TabularList.prototype.events = {
      'click span.pagelink': 'turnPage'
    };

    TabularList.prototype.initialize = function(options) {
      this.collection = options.collection;
      return this.columns = options.columns;
    };

    TabularList.prototype.render = function() {
      var pag,
        _this = this;
      $(this.el).html($("<tr/>").html(_.map(this.columns, function(c) {
        return "<th>" + c.heading + "</td>";
      }).join("")));
      this.collection.each(function(obj) {
        var col, tr, _i, _len, _ref;
        tr = $("<tr/>");
        _ref = _this.columns;
        for (_i = 0, _len = _ref.length; _i < _len; _i++) {
          col = _ref[_i];
          tr.append($("<td/>").append(col.render(obj)));
        }
        return $(_this.el).append(tr);
      });
      if (this.collection.length === 0) {
        $(this.el).append($("<tr/>").append($("<td/>").html("No results").attr("colspan", this.columns.length)));
      } else if (this.collection.pagination != null) {
        pag = $("<td/>").attr({
          colspan: this.columns.length
        });
        pag.addClass("pagination");
        $(this.el).append($("<tr/>").html(pag));
        this.renderPagination(this.collection, pag);
      }
      return this;
    };

    TabularList.prototype.turnPage = function(event) {
      var _this = this;
      this.collection.filter.page = this.newPageFromEvent(event);
      $(this.el).addClass(".loading");
      this.setPageLoading();
      return this.collection.fetch({
        success: function() {
          _this.render();
          return $(_this.el).removeClass(".loading");
        },
        error: function() {
          alert("Server error");
          return $(_this.el).removeClass(".loading");
        }
      });
    };

    TabularList.prototype.dateColumn = function(name, heading) {
      if (heading == null) heading = "Date";
      return {
        heading: heading,
        render: function(obj) {
          return btb.formatDate(obj.get(name));
        }
      };
    };

    return TabularList;

  })(btb.PaginatedView);

  btb.LiveCheckbox = (function(_super) {

    __extends(LiveCheckbox, _super);

    function LiveCheckbox() {
      this.save = __bind(this.save, this);
      this.render = __bind(this.render, this);
      LiveCheckbox.__super__.constructor.apply(this, arguments);
    }

    LiveCheckbox.prototype.tagName = 'input';

    LiveCheckbox.prototype.initialize = function(options) {
      this.model = options.model;
      return this.field = options.field;
    };

    LiveCheckbox.prototype.events = {
      'click': 'save'
    };

    LiveCheckbox.prototype.render = function() {
      $(this.el).attr({
        type: "checkbox",
        checked: !!this.model.get(this.field),
        "class": "editor"
      });
      return this;
    };

    LiveCheckbox.prototype.save = function() {
      var attrs,
        _this = this;
      attrs = {};
      attrs[this.field] = $(this.el).is(":checked");
      this.model.set(attrs);
      return this.model.save({}, {
        success: function(model, response) {
          return $(_this.el).parent().effect("highlight");
        },
        error: function() {
          $(_this.el).parent().addClass("ui-state-error");
          return alert("Server error.");
        }
      });
    };

    return LiveCheckbox;

  })(Backbone.View);

  btb.EditInPlace = (function(_super) {

    __extends(EditInPlace, _super);

    function EditInPlace() {
      this.save = __bind(this.save, this);
      this.renderEditor = __bind(this.renderEditor, this);
      this.render = __bind(this.render, this);
      EditInPlace.__super__.constructor.apply(this, arguments);
    }

    EditInPlace.prototype.tagName = 'span';

    EditInPlace.prototype.template = _.template($("#editInPlace").html() || "");

    EditInPlace.prototype.editorTemplate = _.template($("#editorInPlace").html() || "");

    EditInPlace.prototype.events = {
      'click span.cancel': 'render',
      'click span.edit-in-place': 'renderEditor',
      'click input.save': 'save'
    };

    EditInPlace.prototype.inputTypes = {
      input: function() {
        return $("<input/>").attr("type", "text");
      },
      textarea: function() {
        return $("<textarea/>");
      }
    };

    EditInPlace.prototype.initialize = function(options) {
      this.model = options.model;
      this.field = options.field;
      this.type = options.type != null ? options.type : "input";
      if (options.commitOnSave !== false) return this.commitOnSave = true;
    };

    EditInPlace.prototype.render = function() {
      $(this.el).html(this.template({
        field: this.model.get(this.field)
      }));
      return this;
    };

    EditInPlace.prototype.renderEditor = function() {
      var input, span;
      span = $(".edit-in-place", this.el);
      span.hide();
      span.after(this.editorTemplate);
      input = this.inputTypes[this.type]();
      input.val(this.model.get(this.field));
      input.addClass("editor");
      $(".edit-tag", this.el).replaceWith(input);
      input.focus();
      return this;
    };

    EditInPlace.prototype.save = function() {
      var attrs,
        _this = this;
      attrs = {};
      attrs[this.field] = $(".editor", this.el).val();
      this.model.set(attrs);
      $(this.el).addClass(".loading");
      if (this.commitOnSave) {
        this.model.save({}, {
          success: function(model, response) {
            $(_this.el).removeClass(".loading");
            _this.model = model;
            return $(_this.el).parent().effect("highlight");
          },
          error: function() {
            $(_this.el).removeClass(".loading");
            $(_this.el).parent().addClass("ui-state-error");
            return alert("Server error");
          }
        });
      }
      return this.render();
    };

    return EditInPlace;

  })(Backbone.View);

  btb.EditInPlace.factory = function(modelsets) {
    var attrs, editor, editors, el, field, model, selector, type, _i, _len, _ref;
    editors = [];
    for (_i = 0, _len = modelsets.length; _i < _len; _i++) {
      _ref = modelsets[_i], model = _ref[0], field = _ref[1], selector = _ref[2], type = 4 <= _ref.length ? __slice.call(_ref, 3) : [];
      attrs = {
        model: model,
        field: field
      };
      if (type.length > 0) attrs.type = type[0];
      if (attrs.type === "checkbox") {
        editor = new btb.LiveCheckbox(attrs);
      } else {
        editor = new btb.EditInPlace(attrs);
      }
      el = editor.render().el;
      $(selector).html(editor.render().el);
      editors.push(editor);
    }
    return editors;
  };

}).call(this);
