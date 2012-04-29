(function() {
  var __hasProp = Object.prototype.hasOwnProperty,
    __extends = function(child, parent) { for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; } function ctor() { this.constructor = child; } ctor.prototype = parent.prototype; child.prototype = new ctor; child.__super__ = parent.prototype; return child; },
    __bind = function(fn, me){ return function(){ return fn.apply(me, arguments); }; },
    __slice = Array.prototype.slice,
    __indexOf = Array.prototype.indexOf || function(item) { for (var i = 0, l = this.length; i < l; i++) { if (i in this && this[i] === item) return i; } return -1; };

  btb.Scan = (function(_super) {

    __extends(Scan, _super);

    function Scan() {
      Scan.__super__.constructor.apply(this, arguments);
    }

    Scan.prototype.url = function() {
      return btb.ScanList.prototype.baseUrl + "/" + this.id;
    };

    Scan.prototype.parse = function(response) {
      return response.results[0];
    };

    return Scan;

  })(Backbone.Model);

  btb.ScanList = (function(_super) {

    __extends(ScanList, _super);

    function ScanList() {
      ScanList.__super__.constructor.apply(this, arguments);
    }

    ScanList.prototype.model = btb.Scan;

    ScanList.prototype.baseUrl = "/scanning/scans.json";

    return ScanList;

  })(btb.FilteredPaginatedCollection);

  btb.ScanSplit = (function(_super) {

    __extends(ScanSplit, _super);

    function ScanSplit() {
      ScanSplit.__super__.constructor.apply(this, arguments);
    }

    ScanSplit.prototype.url = function() {
      return "/scanning/scansplits.json/" + this.get("scan").id;
    };

    return ScanSplit;

  })(Backbone.Model);

  btb.ProcessingManager = (function(_super) {

    __extends(ProcessingManager, _super);

    function ProcessingManager() {
      this.render = __bind(this.render, this);
      ProcessingManager.__super__.constructor.apply(this, arguments);
    }

    ProcessingManager.prototype.template = _.template($("#processManager").html());

    ProcessingManager.prototype.initialize = function() {
      this.scanView = new btb.ProcessScanListView();
      return this.docView = new btb.ProcessDocListView();
    };

    ProcessingManager.prototype.render = function() {
      $(this.el).html(this.template());
      $(".process-scan-list", this.el).html(this.scanView.render().el);
      $(".process-document-list", this.el).html(this.docView.render().el);
      return this;
    };

    return ProcessingManager;

  })(Backbone.View);

  btb.ProcessItemListView = (function(_super) {

    __extends(ProcessItemListView, _super);

    function ProcessItemListView() {
      this.turnPage = __bind(this.turnPage, this);
      this.stopLoading = __bind(this.stopLoading, this);
      this.startLoading = __bind(this.startLoading, this);
      this.fetch = __bind(this.fetch, this);
      ProcessItemListView.__super__.constructor.apply(this, arguments);
    }

    ProcessItemListView.prototype.itemTemplate = _.template($("#processItem").html());

    ProcessItemListView.prototype.events = {
      "click span.pagelink": "turnPage"
    };

    ProcessItemListView.prototype.defaultFilter = {};

    ProcessItemListView.prototype.initialize = function(options) {
      if (options == null) {
        options = {
          listClass: btb.DocumentList
        };
      }
      this.list = new options.listClass();
      return this.list.filter = _.extend({}, this.defaultFilter);
    };

    ProcessItemListView.prototype.fetch = function() {
      var _this = this;
      this.startLoading();
      return this.list.fetch({
        success: function() {
          _this.stopLoading();
          return _this.renderDetails();
        },
        error: function() {
          _this.stopLoading();
          return alert("Server error");
        }
      });
    };

    ProcessItemListView.prototype.startLoading = function() {
      return $(this.el).addClass("loading");
    };

    ProcessItemListView.prototype.stopLoading = function() {
      return $(this.el).removeClass("loading");
    };

    ProcessItemListView.prototype.render = function() {
      $(this.el).html("<ul class='process-list'></ul><div class='pagination'></div>");
      this.fetch();
      return this;
    };

    ProcessItemListView.prototype.renderDetails = function() {
      var html, obj, _i, _len, _ref;
      html = '';
      if (this.list.models.length === 0) {
        $('ul', this.el).html("<li>None found.</li>");
      } else {
        _ref = this.list.models;
        for (_i = 0, _len = _ref.length; _i < _len; _i++) {
          obj = _ref[_i];
          html += this.itemTemplate({
            obj: obj.toJSON()
          });
        }
        $('ul', this.el).html(html);
      }
      return this.renderPagination(this.list, $(".pagination", this.el));
    };

    ProcessItemListView.prototype.turnPage = function(event) {
      var page;
      page = this.newPageFromEvent(event);
      this.list.filter.page = page;
      return this.fetch();
    };

    return ProcessItemListView;

  })(btb.PaginatedView);

  btb.ProcessDocListView = (function(_super) {

    __extends(ProcessDocListView, _super);

    function ProcessDocListView() {
      this.renderDetails = __bind(this.renderDetails, this);
      ProcessDocListView.__super__.constructor.apply(this, arguments);
    }

    ProcessDocListView.prototype.defaultFilter = {
      page: 1,
      per_page: 6,
      status: "unknown"
    };

    ProcessDocListView.prototype.initialize = function() {
      return ProcessDocListView.__super__.initialize.call(this, {
        listClass: btb.DocumentList
      });
    };

    ProcessDocListView.prototype.renderDetails = function() {
      ProcessDocListView.__super__.renderDetails.call(this);
      $(".delete-scan", this.el).remove();
      return this;
    };

    return ProcessDocListView;

  })(btb.ProcessItemListView);

  btb.ProcessScanListView = (function(_super) {

    __extends(ProcessScanListView, _super);

    function ProcessScanListView() {
      ProcessScanListView.__super__.constructor.apply(this, arguments);
    }

    ProcessScanListView.prototype.defaultFilter = {
      page: 1,
      per_page: 6,
      processing_complete: 0,
      managed: 1
    };

    ProcessScanListView.prototype.initialize = function() {
      return ProcessScanListView.__super__.initialize.call(this, {
        listClass: btb.ScanList
      });
    };

    return ProcessScanListView;

  })(btb.ProcessItemListView);

  btb.SplitScanView = (function(_super) {

    __extends(SplitScanView, _super);

    function SplitScanView() {
      this.switchToDocumentView = __bind(this.switchToDocumentView, this);
      this.getEditableDocuments = __bind(this.getEditableDocuments, this);
      this.setPageScale = __bind(this.setPageScale, this);
      this.setPageSize = __bind(this.setPageSize, this);
      this.scrollTo = __bind(this.scrollTo, this);
      this.jumpToPage = __bind(this.jumpToPage, this);
      this.nextPage = __bind(this.nextPage, this);
      this.prevPage = __bind(this.prevPage, this);
      this.chooseUser = __bind(this.chooseUser, this);
      this.setIgnore = __bind(this.setIgnore, this);
      this.buildScroller = __bind(this.buildScroller, this);
      this.chooseCode = __bind(this.chooseCode, this);
      this.render = __bind(this.render, this);
      this.checkFinished = __bind(this.checkFinished, this);
      this.setDirty = __bind(this.setDirty, this);
      this.updateType = __bind(this.updateType, this);
      this.selectPage = __bind(this.selectPage, this);
      this.mouseOverPage = __bind(this.mouseOverPage, this);
      this.removeChoice = __bind(this.removeChoice, this);
      this.addPhotoChoice = __bind(this.addPhotoChoice, this);
      this.addPostChoice = __bind(this.addPostChoice, this);
      this.userAddChoice = __bind(this.userAddChoice, this);
      this.addChoice = __bind(this.addChoice, this);
      this.getUnassignedIds = __bind(this.getUnassignedIds, this);
      this.getAssignedIds = __bind(this.getAssignedIds, this);
      this.save = __bind(this.save, this);
      this.loadSplit = __bind(this.loadSplit, this);
      this.keyUp = __bind(this.keyUp, this);
      this.initSplit = __bind(this.initSplit, this);
      SplitScanView.__super__.constructor.apply(this, arguments);
    }

    SplitScanView.prototype.template = _.template($("#splitScan").html());

    SplitScanView.prototype.lockTemplate = _.template($("#splitScanEditLockWarning").html());

    SplitScanView.prototype.minimumTypes = ["post", "profile", "photo", "request", "license"];

    SplitScanView.prototype.addableTypes = ["post", "profile", "photo", "request"];

    SplitScanView.prototype.typeColors = {
      "post": ["#0f0", "#00f", "#0a0", "#00a"],
      "profile": ["#0ff"],
      "photo": ["#f0f", "#a0a", "#606"],
      "request": ["#f00"],
      "license": ["#ff0"],
      "ignore": ["#000"]
    };

    SplitScanView.prototype.events = {
      'click .switch-to-edit-documents': 'switchToDocumentView',
      'mouseover div.page-image': 'mouseOverPage',
      'click .next': 'nextPage',
      'click .prev': 'prevPage',
      'click .pagestatus': 'jumpToPage',
      'click .add-post': 'addPostChoice',
      'click .add-photo': 'addPhotoChoice',
      'click .save': 'save',
      'click .page-size-chooser span': 'setPageSize',
      'keyup .choose-code input': 'chooseCode'
    };

    SplitScanView.prototype.initialize = function(scanId) {
      this.split = new btb.ScanSplit({
        scan: {
          id: parseInt(scanId)
        }
      });
      this.split.fetch({
        success: this.initSplit
      });
      $(window).keyup(this.keyUp);
      this.imgScale = 1;
      return this;
    };

    SplitScanView.prototype.initSplit = function(model) {
      this.loadSplit(model);
      this.render();
      this.setDirty(false);
      this.checkFinished();
      return this.selectPage(0);
    };

    SplitScanView.prototype.keyUp = function(event) {
      var index, _ref;
      if ($("input:focus, textarea:focus").length > 0) return;
      switch (event.keyCode) {
        case 32:
        case 78:
        case 39:
          return this.nextPage(event);
        case 8:
        case 80:
        case 37:
          return this.prevPage(event);
        case 61:
        case 187:
          return this.addPostChoice(event);
        case 220:
          return this.addPhotoChoice(event);
        case 73:
        case 192:
          return this.ignoreView._toggleChoice(event);
        default:
          if ((48 <= (_ref = event.keyCode) && _ref <= 57)) {
            index = (event.keyCode - 48) - 1;
            if (index === -1) index = 9;
            if (index < this.choiceViews.length) {
              return this.choiceViews[index]._toggleChoice(event);
            }
          }
      }
    };

    SplitScanView.prototype.loadSplit = function(split) {
      var doc, type, _i, _j, _len, _len2, _ref, _ref2;
      this.split = split;
      this.choices = [];
      this.typeCount = {};
      _ref = this.split.get("documents");
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        doc = _ref[_i];
        this.addChoice(new btb.Document(doc));
      }
      _ref2 = this.minimumTypes;
      for (_j = 0, _len2 = _ref2.length; _j < _len2; _j++) {
        type = _ref2[_j];
        if (!(this.typeCount[type] != null)) {
          this.addChoice(new btb.Document({
            type: type
          }));
        }
      }
      this.ignoreChoice = new btb.Document({
        pages: [],
        choiceTitle: "ignore"
      });
      if (this.split.get("scan").processing_complete) {
        return this.ignoreChoice.set({
          pages: this.getUnassignedIds()
        });
      }
    };

    SplitScanView.prototype.save = function(event) {
      var _this = this;
      if ($(".save", this.el).hasClass("disabled")) {
        $(".post-save-message", this.el).html("Not savable yet.").removeClass("success").removeClass("warn");
        setTimeout(function() {
          return $(".post-save-message", _this.el).html("");
        }, 2000);
        return;
      }
      this.checkFinished();
      this.split.set({
        "documents": this.choices
      });
      $(".save", this.el).addClass("loading");
      return this.split.save({}, {
        success: function(model) {
          $(".save", _this.el).removeClass("loading");
          _this.initSplit(model);
          if (_this.split.get("scan").processing_complete) {
            return $(".post-save-message", _this.el).html("&check; All good.").addClass("success");
          } else {
            return $(".post-save-message", _this.el).html("Saved, but still needs attention").addClass("warn");
          }
        },
        error: function(model, error) {
          alert("Server error");
          return $(".save", _this.el).removeClass("loading");
        }
      });
    };

    SplitScanView.prototype.getAssignedIds = function() {
      var c;
      return _.union.apply(_, [this.ignoreChoice.get("pages")].concat(__slice.call((function() {
        var _i, _len, _ref, _results;
        _ref = this.choices;
        _results = [];
        for (_i = 0, _len = _ref.length; _i < _len; _i++) {
          c = _ref[_i];
          if (c.get("pages") != null) _results.push(c.get("pages"));
        }
        return _results;
      }).call(this))));
    };

    SplitScanView.prototype.getUnassignedIds = function() {
      var assignedIds, p, pageIds, _i, _len, _ref;
      pageIds = [];
      _ref = this.split.get("scan").pages;
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        p = _ref[_i];
        pageIds.push(p.id);
      }
      assignedIds = this.getAssignedIds();
      return _.difference(pageIds, assignedIds);
    };

    SplitScanView.prototype.addChoice = function(doc) {
      var title, type;
      type = doc.get("type");
      this.typeCount[type] = (this.typeCount[type] || 0) + 1;
      title = type;
      if (this.typeCount[type] > 1) title += " " + this.typeCount[type];
      doc.set({
        choiceTitle: title
      });
      return this.choices.push(doc);
    };

    SplitScanView.prototype.userAddChoice = function(type) {
      var doc;
      doc = new btb.Document({
        type: type
      });
      if (this.currentPageIndex != null) {
        doc.set({
          "pages": [this.split.get("scan").pages[this.currentPageIndex].id]
        });
      }
      this.addChoice(doc);
      this.render();
      this.checkFinished();
      if (this.currentPageIndex != null) {
        return this.selectPage(this.currentPageIndex);
      }
    };

    SplitScanView.prototype.addPostChoice = function(event) {
      return this.userAddChoice("post");
    };

    SplitScanView.prototype.addPhotoChoice = function(event) {
      return this.userAddChoice("photo");
    };

    SplitScanView.prototype.removeChoice = function(type) {
      return alert("TODO");
    };

    SplitScanView.prototype.mouseOverPage = function(event) {
      var i;
      i = parseInt($("input[name=page-index]", event.currentTarget).val());
      return this.selectPage(i);
    };

    SplitScanView.prototype.selectPage = function(pageIndex) {
      var pages, view, _i, _len, _ref;
      this.currentPageIndex = pageIndex;
      $(".in-viewport", this.el).removeClass("in-viewport");
      $(".page-" + pageIndex, this.el).addClass("in-viewport");
      pages = this.split.get("scan").pages;
      $(".current-page", this.el).html("Page " + (pageIndex + 1) + "/" + pages.length);
      _ref = this.choiceViews;
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        view = _ref[_i];
        view.setDisplay(pages[pageIndex].id);
      }
      return this.ignoreView.setDisplay(pages[pageIndex].id);
    };

    SplitScanView.prototype.updateType = function(doc, value) {
      var id, pages;
      this.setDirty(true);
      if (this.currentPageIndex != null) {
        id = this.split.get("scan").pages[this.currentPageIndex].id;
        pages = doc.get("pages") || [];
        if (value && __indexOf.call(pages, id) < 0) {
          pages.push(id);
        } else if (!value) {
          pages = _.select(pages, function(n) {
            return n !== id;
          });
        }
        doc.set({
          pages: pages
        });
        return this.checkFinished();
      }
    };

    SplitScanView.prototype.setDirty = function(val) {
      var saveEnabled, _ref;
      this.dirty = val;
      saveEnabled = this.dirty && (((_ref = this.split.get("scan").author) != null ? _ref.id : void 0) != null);
      $(".save", this.el).toggleClass("disabled", !saveEnabled);
      return $(".switch-to-edit-documents", this.el).toggleClass("disabled", this.dirty || !this.split.get("scan").processing_complete || this.getEditableDocuments().length === 0);
    };

    SplitScanView.prototype.checkFinished = function() {
      var assigned, choice, color, colors, finished, id, type, typeMod, _i, _j, _k, _l, _len, _len2, _len3, _len4, _len5, _m, _ref, _ref2, _ref3, _ref4;
      assigned = this.getAssignedIds();
      $(".pagestatus").removeClass("assigned");
      $(".pagestatus .overlay").css("background-image", "none");
      for (_i = 0, _len = assigned.length; _i < _len; _i++) {
        id = assigned[_i];
        $("#status" + id).addClass("assigned");
      }
      colors = {};
      typeMod = {};
      _ref = this.choices;
      for (_j = 0, _len2 = _ref.length; _j < _len2; _j++) {
        choice = _ref[_j];
        type = choice.get("type");
        typeMod[type] = typeMod[type] != null ? typeMod[type] + 1 : 0;
        _ref2 = choice.get("pages") || [];
        for (_k = 0, _len3 = _ref2.length; _k < _len3; _k++) {
          id = _ref2[_k];
          if (!(colors[id] != null)) colors[id] = [];
          color = this.typeColors[type][typeMod[type] % this.typeColors[type].length];
          colors[id].push(color);
        }
      }
      _ref3 = this.ignoreChoice.get("pages") || [];
      for (_l = 0, _len4 = _ref3.length; _l < _len4; _l++) {
        id = _ref3[_l];
        colors[id] = [this.typeColors.ignore[0]];
      }
      for (_m = 0, _len5 = assigned.length; _m < _len5; _m++) {
        id = assigned[_m];
        btb.colorStripes.apply(btb, ["#status" + id + " .overlay"].concat(__slice.call(colors[id])));
      }
      finished = this.getUnassignedIds().length === 0 && (((_ref4 = this.split.get("scan").author) != null ? _ref4.id : void 0) != null);
      this.split.get("scan").processing_complete = finished;
      return finished;
    };

    SplitScanView.prototype.render = function() {
      var choice, choiceView, lock, scan, user, _i, _len, _ref,
        _this = this;
      scan = this.split.get("scan");
      if (scan.pages != null) {
        $(this.el).html(this.template({
          scan: scan
        }));
        if (scan.author) {
          user = new btb.User(scan.author);
        } else {
          user = null;
        }
        this.userToggle = new btb.InPlaceUserChooser(user);
        this.userToggle.bind("chosen", function(user) {
          _this.chooseUser(user);
          return _this.setDirty(true);
        });
        $(".user-chooser-holder", this.el).html(this.userToggle.render().el);
        $(".user-chooser-trigger", this.el).attr("placeholder", "Author");
        this.ignoreView = new btb.SplitScanPageDocChoice({
          choice: this.ignoreChoice
        });
        this.ignoreView.bind("toggleChoice", function(choice, value) {
          _this.updateType(choice, value);
          return _this.setIgnore(value);
        });
        $(".ignore-choice", this.el).append(this.ignoreView.render().el);
        this.choiceViews = [];
        _ref = this.choices;
        for (_i = 0, _len = _ref.length; _i < _len; _i++) {
          choice = _ref[_i];
          choiceView = new btb.SplitScanPageDocChoice({
            choice: choice
          });
          choiceView.bind("toggleChoice", function(choice, value) {
            _this.updateType(choice, value);
            if (value) {
              _this.updateType(_this.ignoreChoice, false);
              return _this.setIgnore(false);
            }
          });
          $(".type-list", this.el).append(choiceView.render().el);
          this.choiceViews.push(choiceView);
        }
        this.buildScroller();
        $(".note-manager", this.el).append(new btb.NoteManager({
          filter: {
            scan_id: scan.id
          },
          defaults: {
            scan_id: scan.id
          }
        }).el);
      }
      if (this.split.get("lock") != null) {
        lock = this.split.get("lock");
        $(".lock-warning", this.el).append(this.lockTemplate({
          name: lock.user.display_name,
          created: lock.created,
          now: lock.now
        }));
      }
      $(".page-image img").load(function() {
        return _this.setPageScale(parseFloat($.cookie("scanpagesize") || 1));
      });
      return this;
    };

    SplitScanView.prototype.chooseCode = function(event) {
      var code,
        _this = this;
      code = $(event.currentTarget).val();
      this.split.get("scan").pendingscan_code = "";
      this.setDirty(true);
      if (!$.trim(code)) {
        $(".choose-code input", this.el).removeClass("error");
        return;
      } else {
        $(event.currentTarget).addClass("loading");
        $.get("/scanning/scancodes.json", {
          term: code
        }, function(data) {
          var ps, _i, _len;
          $(event.currentTarget).removeClass("loading");
          for (_i = 0, _len = data.length; _i < _len; _i++) {
            ps = data[_i];
            if (ps.code === code) {
              $(".choose-code input", _this.el).removeClass("error");
              _this.userToggle.setUser(new btb.User(ps.author));
              _this.split.get("scan").pendingscan_code = code;
              return;
            }
          }
        });
      }
      return $(".choose-code input", this.el).addClass("error");
    };

    SplitScanView.prototype.buildScroller = function() {
      var aspect, best, height, n, numCols, numRows, pageHeight, pageWidth, perCol, perRow, waste, wastedSpace, width;
      n = this.split.get("scan").pages.length;
      width = $(".page-scroller", this.el).width();
      height = $(".page-scroller", this.el).height();
      aspect = 11 / 8.5;
      best = {};
      wastedSpace = 100000000000;
      for (numRows = 1; 1 <= n ? numRows <= n : numRows >= n; 1 <= n ? numRows++ : numRows--) {
        perRow = Math.ceil(n / numRows);
        pageHeight = Math.min(height, Math.floor(height / numRows));
        pageWidth = Math.floor(pageHeight / aspect);
        if (pageHeight * numRows > height || pageWidth * perRow > width) continue;
        waste = height * width - (pageHeight * pageWidth * n);
        if (waste < wastedSpace) {
          wastedSpace = waste;
          best = {
            strategy: "row",
            numRows: numRows,
            numCols: perRow,
            pageHeight: pageHeight,
            pageWidth: pageWidth
          };
        }
      }
      for (numCols = 1; 1 <= n ? numCols <= n : numCols >= n; 1 <= n ? numCols++ : numCols--) {
        perCol = Math.ceil(n / numCols);
        pageWidth = Math.min(width, Math.floor(width / numCols));
        pageHeight = Math.floor(pageWidth * aspect);
        if ((pageWidth * numCols) > width || (pageHeight * perCol) > height) {
          continue;
        }
        waste = height * width - (pageHeight * pageWidth * n);
        if (waste < wastedSpace) {
          wastedSpace = waste;
          best = {
            strategy: "col",
            numRows: perCol,
            numCols: numCols,
            pageHeight: pageHeight,
            pageWidth: pageWidth
          };
        }
      }
      $(".pagestatus", this.el).width(best.pageWidth - 2);
      $(".pagestatus", this.el).height(best.pageHeight - 2);
      return $(".page-scroller", this.el).height(best.pageHeight * best.numRows);
    };

    SplitScanView.prototype.setIgnore = function(value) {
      var view, _i, _len, _ref, _results;
      if (value) {
        _ref = this.choiceViews;
        _results = [];
        for (_i = 0, _len = _ref.length; _i < _len; _i++) {
          view = _ref[_i];
          this.updateType(view.choice, false);
          _results.push((function() {
            var _j, _len2, _ref2, _results2;
            _ref2 = this.choiceViews;
            _results2 = [];
            for (_j = 0, _len2 = _ref2.length; _j < _len2; _j++) {
              view = _ref2[_j];
              _results2.push(view.toggleChoice(false, true));
            }
            return _results2;
          }).call(this));
        }
        return _results;
      } else {
        return this.ignoreView.toggleChoice(false, true);
      }
    };

    SplitScanView.prototype.chooseUser = function(user) {
      return this.split.get("scan").author = user.toJSON();
    };

    SplitScanView.prototype.prevPage = function(event) {
      return this.scrollTo((this.currentPageIndex || 0) - 1);
    };

    SplitScanView.prototype.nextPage = function(event) {
      return this.scrollTo((this.currentPageIndex || 0) + 1);
    };

    SplitScanView.prototype.jumpToPage = function(event) {
      var classes, index, match, name, _i, _len;
      classes = event.currentTarget.className.split(/\s+/);
      for (_i = 0, _len = classes.length; _i < _len; _i++) {
        name = classes[_i];
        match = /page-(\d+)/.exec(name);
        if (match) {
          index = parseInt(match[1]);
          this.scrollTo(index);
          return;
        }
      }
    };

    SplitScanView.prototype.scrollTo = function(pageIndex) {
      var target;
      if ((0 <= pageIndex && pageIndex < this.split.get("scan").pages.length)) {
        target = $(".page-image.page-" + pageIndex, this.el);
        $('html,body').animate({
          scrollTop: target.offset().top
        }, 200);
        return this.selectPage(pageIndex);
      }
    };

    SplitScanView.prototype.pageSizes = {
      small: 0.2,
      medium: 0.5,
      large: 1.0
    };

    SplitScanView.prototype.setPageSize = function(event) {
      var newScale;
      $(event.currentTarget).removeClass("chosen");
      newScale = this.pageSizes[event.currentTarget.className];
      return this.setPageScale(newScale);
    };

    SplitScanView.prototype.setPageScale = function(newScale) {
      var el, h, name, page, scale, w, _i, _len, _ref, _ref2;
      $(".page-size-chooser span", this.el).removeClass("chosen");
      _ref = this.pageSizes;
      for (name in _ref) {
        scale = _ref[name];
        if (scale === newScale) {
          $(".page-size-chooser ." + name, this.el).addClass("chosen");
        }
      }
      _ref2 = this.split.get("scan").pages;
      for (_i = 0, _len = _ref2.length; _i < _len; _i++) {
        page = _ref2[_i];
        w = Math.min(page.image_dims[0], 900);
        h = w / page.image_dims[0] * page.image_dims[1];
        el = $(".page-image.page-" + page.order, this.el).width(w * newScale).height(h * newScale);
        el.find("img").css({
          width: "100%",
          height: "100%"
        });
      }
      this.imgScale = newScale;
      return $.cookie("scanpagesize", newScale);
    };

    SplitScanView.prototype.getEditableDocuments = function() {
      var _this = this;
      return _.select(this.choices, function(c) {
        var _ref;
        return ((_ref = c.get("pages")) != null ? _ref.length : void 0) > 0;
      });
    };

    SplitScanView.prototype.switchToDocumentView = function() {
      var editableIds;
      if ($(".switch-to-edit-documents", this.el).hasClass("disabled")) return;
      editableIds = _.pluck(this.getEditableDocuments(), "id");
      return btb.app.navigate("#/process/document/" + (editableIds.join(".")), true);
    };

    return SplitScanView;

  })(Backbone.View);

  btb.SplitScanPageDocChoice = (function(_super) {

    __extends(SplitScanPageDocChoice, _super);

    function SplitScanPageDocChoice() {
      this.chosenIds = __bind(this.chosenIds, this);
      this.setDisplay = __bind(this.setDisplay, this);
      this.toggleChoice = __bind(this.toggleChoice, this);
      this._toggleChoice = __bind(this._toggleChoice, this);
      this.render = __bind(this.render, this);
      SplitScanPageDocChoice.__super__.constructor.apply(this, arguments);
    }

    SplitScanPageDocChoice.prototype.tagName = "li";

    SplitScanPageDocChoice.prototype.template = _.template($("#splitScanPageDocChoice").html());

    SplitScanPageDocChoice.prototype.events = {
      'click': '_toggleChoice'
    };

    SplitScanPageDocChoice.prototype.initialize = function(_arg) {
      var choice, chosen;
      choice = _arg.choice, chosen = _arg.chosen;
      this.choice = choice;
      return this.chosen = chosen || false;
    };

    SplitScanPageDocChoice.prototype.render = function() {
      $(this.el).html(this.template({
        title: this.choice.get("choiceTitle"),
        chosen: this.chosen
      }));
      return this;
    };

    SplitScanPageDocChoice.prototype._toggleChoice = function(event) {
      return this.toggleChoice(null, null);
    };

    SplitScanPageDocChoice.prototype.toggleChoice = function(value, silent) {
      this.chosen = value != null ? value : !this.chosen;
      this.render();
      if (!silent) return this.trigger("toggleChoice", this.choice, this.chosen);
    };

    SplitScanPageDocChoice.prototype.setDisplay = function(pageId) {
      this.chosen = __indexOf.call(this.chosenIds(), pageId) >= 0;
      return this.render();
    };

    SplitScanPageDocChoice.prototype.chosenIds = function() {
      return this.choice.get("pages") || [];
    };

    return SplitScanPageDocChoice;

  })(Backbone.View);

}).call(this);
