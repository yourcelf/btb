(function() {
  var Cropper;
  var __hasProp = Object.prototype.hasOwnProperty, __extends = function(child, parent) {
    for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; }
    function ctor() { this.constructor = child; }
    ctor.prototype = parent.prototype;
    child.prototype = new ctor;
    child.__super__ = parent.prototype;
    return child;
  }, __bind = function(fn, me){ return function(){ return fn.apply(me, arguments); }; }, __indexOf = Array.prototype.indexOf || function(item) {
    for (var i = 0, l = this.length; i < l; i++) {
      if (this[i] === item) return i;
    }
    return -1;
  };
  btb.Document = (function() {
    __extends(Document, Backbone.Model);
    function Document() {
      Document.__super__.constructor.apply(this, arguments);
    }
    Document.prototype.url = function() {
      return btb.DocumentList.prototype.baseUrl + "/" + this.id;
    };
    return Document;
  })();
  btb.DocumentList = (function() {
    __extends(DocumentList, btb.FilteredPaginatedCollection);
    function DocumentList() {
      DocumentList.__super__.constructor.apply(this, arguments);
    }
    DocumentList.prototype.model = btb.Document;
    DocumentList.prototype.baseUrl = "/scanning/documents.json";
    return DocumentList;
  })();
  btb.EditDocumentManager = (function() {
    __extends(EditDocumentManager, Backbone.View);
    function EditDocumentManager() {
      this.render = __bind(this.render, this);
      EditDocumentManager.__super__.constructor.apply(this, arguments);
    }
    EditDocumentManager.prototype.template = _.template($("#editDocumentsManager").html());
    EditDocumentManager.prototype.initialize = function(options) {
      if (options == null) {
        options = {
          documents: []
        };
      }
      this.documents = new btb.DocumentList;
      this.documents.filter.idlist = options.documents.join(".");
      return this.documents.fetch({
        success: this.render
      });
    };
    EditDocumentManager.prototype.render = function() {
      var doc, docview, i, _i, _len, _ref;
      if (this.documents.length > 0) {
        $(this.el).html(this.template({
          numdocs: this.documents.length
        }));
        i = 0;
        _ref = this.documents.models;
        for (_i = 0, _len = _ref.length; _i < _len; _i++) {
          doc = _ref[_i];
          docview = new btb.EditDocumentView({
            doc: doc,
            num: this.documents.length,
            order: i
          });
          i++;
          $(".document-list", this.el).append(docview.render().el);
        }
      }
      return this;
    };
    return EditDocumentManager;
  })();
  btb.EditDocumentView = (function() {
    __extends(EditDocumentView, Backbone.View);
    function EditDocumentView() {
      this.checkInReplyToCode = __bind(this.checkInReplyToCode, this);
      this.setPageSize = __bind(this.setPageSize, this);
      this.pageSizeFull = __bind(this.pageSizeFull, this);
      this.pageSizeMedium = __bind(this.pageSizeMedium, this);
      this.pageSizeSmall = __bind(this.pageSizeSmall, this);
      this.swapPages = __bind(this.swapPages, this);
      this.save = __bind(this.save, this);
      this.render = __bind(this.render, this);
      EditDocumentView.__super__.constructor.apply(this, arguments);
    }
    EditDocumentView.prototype.template = _.template($("#editDocument").html());
    EditDocumentView.prototype.inReplyToTemplate = _.template($("#editDocumentInReplyTo").html());
    EditDocumentView.prototype.pageSizes = {
      small: 0.3,
      medium: 0.6,
      full: 1
    };
    EditDocumentView.prototype.events = {
      'click .small': 'pageSizeSmall',
      'click .medium': 'pageSizeMedium',
      'click .full': 'pageSizeFull',
      'click .save-doc': 'save',
      'keyup .doc-in-reply-to': 'checkInReplyToCode'
    };
    EditDocumentView.prototype.initialize = function(options) {
      if (options == null) {
        options = {
          doc: null,
          num: 1,
          order: 0
        };
      }
      this.doc = options.doc;
      this.num = options.num;
      return this.order = options.order;
    };
    EditDocumentView.prototype.render = function() {
      var changeTags, page, userChooser, _fn, _i, _len, _ref;
      $(this.el).html(this.template({
        doc: this.doc.toJSON(),
        num: this.num,
        order: this.order
      }));
      this.pageViews = [];
      _ref = _.sortBy(this.doc.get("pages"), function(p) {
        return p.order;
      });
      _fn = __bind(function(page) {
        var ht, pv;
        pv = new btb.EditDocumentPageView({
          page: page,
          pagecount: this.doc.get("pages").length
        });
        ht = this.doc.get("highlight_transform");
        if (page.id === (ht != null ? ht.document_page_id : void 0)) {
          pv.setHighlightRelativeToCrop(ht.crop);
        }
        pv.bind("highlightChanged", __bind(function(crop) {
          var view, _j, _len2, _ref2, _results;
          if (crop) {
            ht = {
              crop: crop,
              document_page_id: pv.page.id
            };
            this.doc.set({
              "highlight_transform": ht
            });
          } else {
            this.doc.set({
              "highlight_transform": null
            });
          }
          _ref2 = this.pageViews;
          _results = [];
          for (_j = 0, _len2 = _ref2.length; _j < _len2; _j++) {
            view = _ref2[_j];
            _results.push(view !== pv ? view.clearHighlight() : void 0);
          }
          return _results;
        }, this));
        pv.bind("movePageUp", __bind(function() {
          return this.swapPages(page.order - 1, page.order);
        }, this));
        pv.bind("movePageDown", __bind(function() {
          return this.swapPages(page.order, page.order + 1);
        }, this));
        pv.bind("cropping", __bind(function(cropping) {
          var view, _j, _len2, _ref2, _results;
          _ref2 = this.pageViews;
          _results = [];
          for (_j = 0, _len2 = _ref2.length; _j < _len2; _j++) {
            view = _ref2[_j];
            _results.push(view !== pv ? view.setCropping(cropping, false) : void 0);
          }
          return _results;
        }, this));
        pv.bind("highlighting", __bind(function(highlighting) {
          var view, _j, _len2, _ref2, _results;
          _ref2 = this.pageViews;
          _results = [];
          for (_j = 0, _len2 = _ref2.length; _j < _len2; _j++) {
            view = _ref2[_j];
            _results.push(view !== pv ? view.setHighlighting(highlighting, false) : void 0);
          }
          return _results;
        }, this));
        this.pageViews.push(pv);
        return $(".page-list", this.el).append(pv.render().el);
      }, this);
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        page = _ref[_i];
        _fn(page);
      }
      userChooser = new btb.InPlaceUserChooser(new btb.User(this.doc.get("author")));
      userChooser.bind("chosen", __bind(function(model) {
        return this.doc.set({
          author: model.toJSON()
        });
      }, this));
      $(".choose-user-holder", this.el).append(userChooser.render().el);
      $(".doc-title", this.el).change(__bind(function() {
        return this.doc.set({
          title: $(".doc-title", this.el).val()
        });
      }, this));
      $(".doc-date", this.el).change(__bind(function() {
        return this.doc.set({
          date_written: $(".doc-date", this.el).val()
        });
      }, this));
      $(".doc-status", this.el).val(this.doc.get("status")).change(__bind(function() {
        return this.doc.set({
          status: $(".doc-status", this.el).val()
        });
      }, this));
      $(".doc-adult", this.el).change(__bind(function() {
        return this.doc.set({
          adult: $(".doc-adult", this.el).is(":checked")
        });
      }, this));
      changeTags = __bind(function() {
        return this.doc.set({
          tags: $(".doc-tags", this.el).val()
        });
      }, this);
      $(".doc-tags", this.el).smartTextBox({
        submitKeys: [13, 188],
        updateOriginal: true,
        debug: true,
        onElementAdd: changeTags,
        onElementRemove: changeTags
      });
      $(".doc-in-reply-to", this.el).change(__bind(function() {
        return this.doc.set({
          in_reply_to: $(".doc-in-reply-to", this.el).val()
        });
      }, this));
      $(".document-notes-manager", this.el).html(new btb.NoteManager({
        filter: {
          document_id: this.doc.id
        },
        defaults: {
          document_id: this.doc.id
        }
      }).el);
      $(".user-notes-table", this.el).html(new btb.NoteViewTable({
        filter: {
          user_id: this.doc.get("author").id,
          important: 1
        }
      }).render().el);
      this.setPageSize();
      switch (this.doc.get("type")) {
        case "request":
          $(".correspondence-list", this.el).html(new btb.CorrespondenceManager({
            recipient: new btb.User(this.doc.get("author"))
          }).el);
          break;
        case "license":
          $(".user-status-table", this.el).html(new btb.UserStatusTable({
            user: new btb.User(this.doc.get("author"))
          }).render().el);
      }
      if (this.doc.get("in_reply_to")) {
        this.checkInReplyToCode();
      }
      return this;
    };
    EditDocumentView.prototype.save = function() {
      var d, error, errors, _i, _len, _ref, _ref2;
      errors = [];
      $(".post-save-message", this.el).html("");
      if (this.doc.get("type") === "post" && !((_ref = this.doc.get("highlight_transform")) != null ? (_ref2 = _ref.crop) != null ? _ref2.length : void 0 : void 0) > 0) {
        errors.push("Please add a highlighted section to a page.");
      }
      d = new Date(this.doc.get("date_written"));
      if (isNaN(d.getTime())) {
        errors.push("Please enter a valid date, in YYYY-MM-DD format.");
        $(".doc-date", this.el).addClass("error");
      } else {
        $(".doc-date", this.el).removeClass("error");
      }
      if (!this.doc.get("author")) {
        errors.push("Please choose an author.");
        $(".choose-user-holder", this.el).addClass("error");
      } else {
        $(".choose-user-holder", this.el).removeClass("error");
      }
      for (_i = 0, _len = errors.length; _i < _len; _i++) {
        error = errors[_i];
        $(".post-save-message", this.el).append("<div class='error'>" + error + "</div>");
      }
      if (errors.length === 0) {
        $(".save-doc", this.el).addClass("loading");
        return this.doc.save({}, {
          success: __bind(function() {
            var klass, msg, status, type;
            $(".save-doc", this.el).removeClass("loading");
            this.render();
            type = this.doc.get("type");
            status = this.doc.get("status");
            if (status === "unknown") {
              klass = "warn";
              msg = "Document saved, but still needs attention.  Add a note explaining why?";
            } else if (status === "published") {
              klass = "success";
              msg = "&check; Document saved and published.";
              if (!this.doc.get("is_public")) {
                klass = "warn";
                msg = "Document saved and marked published, but author is not active or enrolled.                                   The document will be published when the author is made active and enrolled.";
              }
              if (this.doc.get("type") === "post" && !this.doc.get("title")) {
                msg += " Title left blank.";
              }
            } else if (status === "unpublishable") {
              klass = "success";
              msg = "Document saved, and marked unpublishable.";
            } else if (status === "ready") {
              klass = "success";
              msg = "Document queued; will be published within 3 days.";
              if (this.doc.get("type") === "post" && !this.doc.get("title")) {
                msg += " Title left blank.";
              }
            }
            return $(".post-save-message", this.el).addClass(klass).html(msg);
          }, this),
          error: __bind(function(model, response) {
            var msg;
            msg = "Server error - not saved. ";
            if ((response != null ? response.responseText : void 0) != null) {
              msg += _.escapeHTML(response.responseText);
              msg += " (code " + response.status + ")";
            }
            $(".save-doc", this.el).removeClass("loading");
            return $(".post-save-message", this.el).addClass("error").html(msg);
          }, this)
        });
      }
    };
    EditDocumentView.prototype.swapPages = function(from, to) {
      var dest, el, frompage, holder, holders, i, offset, offsets, p, p2, page, pages, topage, _i, _len, _ref, _ref2, _ref3, _ref4, _results;
      frompage = _.select(this.pageViews, function(pv) {
        return pv.page.order === from;
      });
      topage = _.select(this.pageViews, function(pv) {
        return pv.page.order === to;
      });
      if (!(frompage.length === 1 && topage.length === 1)) {
        return;
      }
      pages = [frompage[0], topage[0]];
      p2 = topage[0];
      _ref = [pages[1].page.order, pages[0].page.order], pages[0].page.order = _ref[0], pages[1].page.order = _ref[1];
      holders = [];
      offsets = (function() {
        var _i, _len, _results;
        _results = [];
        for (_i = 0, _len = pages.length; _i < _len; _i++) {
          p = pages[_i];
          _results.push($(p.el).offset().top);
        }
        return _results;
      })();
      for (i = 0, _ref2 = pages.length; 0 <= _ref2 ? i < _ref2 : i > _ref2; 0 <= _ref2 ? i++ : i--) {
        offset = offsets[i];
        page = pages[i];
        el = $(page.el);
        holder = $("<div/>").attr("class", "swap-placeholder").width(el.width()).height(el.height()).css({
          "background-color": "#eee",
          "z-index": 1
        });
        el.after(holder).css({
          position: 'absolute',
          top: offset.top,
          left: offset.left,
          zIndex: 1000,
          opacity: 0.8
        });
        holders.push(holder);
      }
      page = pages[0];
      dest = holders[1];
      _ref3 = [[pages[0], holders[1]], [pages[1], holders[0]]];
      _results = [];
      for (_i = 0, _len = _ref3.length; _i < _len; _i++) {
        _ref4 = _ref3[_i], page = _ref4[0], dest = _ref4[1];
        _results.push(__bind(function(page, dest) {
          return $(page.el).animate({
            top: dest.position().top,
            left: dest.position().left
          }, 'slow', 'swing', __bind(function() {
            $(page.el).css({
              position: 'static',
              top: 'auto',
              left: 'auto',
              zIndex: 'auto',
              opacity: 1
            }).insertAfter(dest);
            dest.remove();
            return page.render();
          }, this));
        }, this)(page, dest));
      }
      return _results;
    };
    EditDocumentView.prototype.pageSizeSmall = function(event) {
      return this.setPageSize(this.pageSizes.small, event);
    };
    EditDocumentView.prototype.pageSizeMedium = function(event) {
      return this.setPageSize(this.pageSizes.medium, event);
    };
    EditDocumentView.prototype.pageSizeFull = function(event) {
      return this.setPageSize(this.pageSizes.full, event);
    };
    EditDocumentView.prototype.setPageSize = function(size, event) {
      var name, pv, val, _i, _len, _ref, _ref2, _results;
      if (size) {
        $.cookie("pagesize", size);
      } else {
        size = parseFloat($.cookie("pagesize") || 1);
      }
      $(".page-size span", this.el).removeClass("active");
      _ref = this.pageSizes;
      for (name in _ref) {
        val = _ref[name];
        if (val === size) {
          $("." + name, this.el).addClass("active");
        }
      }
      _ref2 = this.pageViews;
      _results = [];
      for (_i = 0, _len = _ref2.length; _i < _len; _i++) {
        pv = _ref2[_i];
        pv.scale = size;
        _results.push(pv.render());
      }
      return _results;
    };
    EditDocumentView.prototype.checkInReplyToCode = function(event) {
      var details, input, update, val;
      input = $(".doc-in-reply-to", this.el);
      details = $(".doc-in-reply-to-details", this.el);
      val = input.val();
      details.html("");
      if (val === "") {
        input.removeClass("error");
        input.removeClass("loading");
        return;
      }
      input.addClass("loading");
      update = __bind(function() {
        return $.ajax({
          url: "/annotations/reply_codes.json",
          type: "GET",
          data: {
            code: val,
            document: 1
          },
          success: __bind(function(data) {
            var error, result;
            input.removeClass("loading");
            if (data.pagination.count !== 1) {
              return input.addClass("error");
            } else {
              result = data.results[0];
              input.removeClass("loading");
              if (this.doc.get("author").id !== result.document.author.id) {
                error = "Warning: document author doesn't match" + " reply author -- wrong reply code?";
              } else {
                input.removeClass("error");
                error = null;
              }
              result.error = error;
              return details.html(this.inReplyToTemplate(data.results[0]));
            }
          }, this),
          error: __bind(function() {
            input.removeClass("loading");
            return alert("Server error");
          }, this)
        });
      }, this);
      if (this.replyCodeTimeout) {
        clearTimeout(this.replyCodeTimeout);
      }
      return setTimeout(update, 100);
    };
    return EditDocumentView;
  })();
  btb.EditDocumentPageView = (function() {
    __extends(EditDocumentPageView, Backbone.View);
    function EditDocumentPageView() {
      this.setHighlightRelativeToCrop = __bind(this.setHighlightRelativeToCrop, this);
      this.highlightRelativeToCrop = __bind(this.highlightRelativeToCrop, this);
      this.clearHighlight = __bind(this.clearHighlight, this);
      this.handleMouse = __bind(this.handleMouse, this);
      this.mouseMove = __bind(this.mouseMove, this);
      this.mouseUp = __bind(this.mouseUp, this);
      this.mouseDown = __bind(this.mouseDown, this);
      this.setHighlighting = __bind(this.setHighlighting, this);
      this.highlight = __bind(this.highlight, this);
      this.setCropping = __bind(this.setCropping, this);
      this.crop = __bind(this.crop, this);
      this.movePageDown = __bind(this.movePageDown, this);
      this.movePageUp = __bind(this.movePageUp, this);
      this._rotate = __bind(this._rotate, this);
      this.rotateTwoSeventy = __bind(this.rotateTwoSeventy, this);
      this.rotateNinety = __bind(this.rotateNinety, this);
      this.rotateR = __bind(this.rotateR, this);
      this.rotateL = __bind(this.rotateL, this);
      this.renderCanvas = __bind(this.renderCanvas, this);
      this.render = __bind(this.render, this);
      EditDocumentPageView.__super__.constructor.apply(this, arguments);
    }
    EditDocumentPageView.prototype.template = _.template($("#editDocumentPage").html());
    EditDocumentPageView.prototype.events = {
      'click .rotate90': 'rotateNinety',
      'click .rotate270': 'rotateTwoSeventy',
      'click .rotateL': 'rotateL',
      'click .rotateR': 'rotateR',
      'click .move-page-up': 'movePageUp',
      'click .move-page-down': 'movePageDown',
      'click .crop': 'crop',
      'click .highlight': 'highlight',
      'mousemove .page-image': 'mouseMove',
      'mousedown .page-image': 'mouseDown'
    };
    EditDocumentPageView.prototype.grabMargin = 4;
    EditDocumentPageView.prototype.scale = 1;
    EditDocumentPageView.prototype.initialize = function(options) {
      if (options == null) {
        options = {
          page: null,
          pagecount: 1
        };
      }
      this.highlight = null;
      this.page = options.page;
      this.page.transformations = this.page.transformations || {};
      this.pagecount = options.pagecount;
      this.cropper = new Cropper("black", "rgba(0, 0, 0, 0.5)");
      this.highlighter = new Cropper("orange", "rgba(0,0,0,0)");
      this.highlighting = true;
      this.mouseIsDown = false;
      return $(document).mouseup(__bind(function(event) {
        if (this.mouseIsDown) {
          return this.mouseUp(event);
        }
      }, this));
    };
    EditDocumentPageView.prototype.render = function() {
      $(this.el).html(this.template({
        page: this.page,
        pagecount: this.pagecount
      }));
      this.canvas = $(".page-image", this.el)[0];
      if (this.cropping) {
        $(".crop", this.el).addClass("active");
        $(".page-image", this.el).css("cursor", "crosshair");
      } else if (this.highlighting) {
        $(".highlight", this.el).addClass("active");
        $(".page-image", this.el).css("cursor", "crosshair");
      } else {
        $(".page-image", this.el).css("cursor", "normal");
      }
      this.img = new Image();
      this.img.onload = __bind(function() {
        return this.renderCanvas();
      }, this);
      this.img.src = this.page.scan_page.image;
      if (this.pagecount - 1 === this.page.order) {
        $(".move-page-down", this.el).hide();
      } else if (this.page.order === 0) {
        $(".move-page-up", this.el).hide();
      }
      return this;
    };
    EditDocumentPageView.prototype.renderCanvas = function() {
      var c, corners, ctx, h, height, maxx, maxy, minx, miny, scale, theta, tx, ty, w, width, x, y, _i, _len, _ref, _ref2, _ref3, _ref4, _ref5;
      theta = (((_ref = this.page.transformations) != null ? _ref.rotate : void 0) || 0) / 360 * 2 * Math.PI;
      _ref2 = this.page.scan_page.image_dims, w = _ref2[0], h = _ref2[1];
      corners = [[0, 0], [w, 0], [0, h], [w, h]];
      for (_i = 0, _len = corners.length; _i < _len; _i++) {
        c = corners[_i];
        x = c[0], y = c[1];
        c[0] = x * Math.cos(-theta) + y * Math.sin(-theta);
        c[1] = y * Math.cos(-theta) - x * Math.sin(-theta);
      }
      minx = _.min(_.pluck(corners, 0));
      miny = _.min(_.pluck(corners, 1));
      maxx = _.max(_.pluck(corners, 0));
      maxy = _.max(_.pluck(corners, 1));
      _ref3 = [-minx, -miny], tx = _ref3[0], ty = _ref3[1];
      _ref4 = [tx * Math.cos(theta) + ty * Math.sin(theta), ty * Math.cos(theta) - tx * Math.sin(theta)], tx = _ref4[0], ty = _ref4[1];
      scale = Math.min(1, 850 / (maxx - minx));
      _ref5 = [(maxx - minx) * scale, (maxy - miny) * scale], width = _ref5[0], height = _ref5[1];
      $(this.canvas).css({
        width: (width * this.scale) + "px",
        height: (height * this.scale) + "px"
      }).attr({
        width: width,
        height: height
      });
      ctx = this.canvas.getContext('2d');
      ctx.clearRect(0, 0, width, height);
      ctx.save();
      ctx.rotate(theta);
      ctx.scale(scale, scale);
      ctx.translate(tx, ty);
      ctx.drawImage(this.img, 0, 0);
      ctx.restore();
      if (this.page.transformations.crop) {
        this.cropper.render(this.canvas, this.page.transformations.crop, this.cropping);
      }
      if (this.highlight) {
        return this.highlighter.render(this.canvas, this.highlight, this.highlighting);
      }
    };
    EditDocumentPageView.prototype.rotateL = function() {
      return this._rotate(359);
    };
    EditDocumentPageView.prototype.rotateR = function() {
      return this._rotate(1);
    };
    EditDocumentPageView.prototype.rotateNinety = function() {
      return this._rotate(90);
    };
    EditDocumentPageView.prototype.rotateTwoSeventy = function() {
      return this._rotate(270);
    };
    EditDocumentPageView.prototype._rotate = function(deg) {
      var newrot, oldrot;
      oldrot = this.page.transformations.rotate || 0;
      newrot = (oldrot + deg) % 360;
      this.page.transformations.rotate = newrot;
      if (this.page.transformations.rotate === 0) {
        delete this.page.transformations.rotate;
      }
      return this.renderCanvas();
    };
    EditDocumentPageView.prototype.movePageUp = function() {
      return this.trigger("movePageUp");
    };
    EditDocumentPageView.prototype.movePageDown = function() {
      return this.trigger("movePageDown");
    };
    EditDocumentPageView.prototype.crop = function() {
      return this.setCropping(!this.cropping);
    };
    EditDocumentPageView.prototype.setCropping = function(cropping, trigger) {
      if (trigger == null) {
        trigger = true;
      }
      this.cropping = cropping;
      if (this.cropping) {
        this.highlighting = false;
      }
      this.render();
      if (trigger) {
        return this.trigger("cropping", this.cropping);
      }
    };
    EditDocumentPageView.prototype.highlight = function() {
      return this.setHighlighting(!this.highlighting);
    };
    EditDocumentPageView.prototype.setHighlighting = function(highlighting, trigger) {
      if (trigger == null) {
        trigger = true;
      }
      this.highlighting = highlighting;
      if (this.highlighting) {
        this.cropping = false;
      }
      this.render();
      if (trigger) {
        return this.trigger("highlighting", this.highlighting);
      }
    };
    EditDocumentPageView.prototype.mouseDown = function(event) {
      this.mouseIsDown = true;
      return this.handleMouse(event, "down");
    };
    EditDocumentPageView.prototype.mouseUp = function(event) {
      this.mouseIsDown = false;
      return this.handleMouse(event, "up");
    };
    EditDocumentPageView.prototype.mouseMove = function(event) {
      return this.handleMouse(event, "move");
    };
    EditDocumentPageView.prototype.handleMouse = function(event, type) {
      var mx, my, offset, orig;
      offset = $(this.canvas).offset();
      mx = (event.pageX - offset.left) / this.scale;
      my = (event.pageY - offset.top) / this.scale;
      if (this.cropping) {
        orig = this.page.transformations.crop;
        this.page.transformations.crop = this.cropper.handleMouse(mx, my, type, this.page.transformations.crop);
        $(this.canvas).css("cursor", this.cropper.cursor);
        if (orig !== this.page.transformations.crop) {
          this.renderCanvas();
          if (this.highlight) {
            return this.trigger("highlightChanged", this.highlightRelativeToCrop());
          }
        }
      } else if (this.highlighting) {
        orig = this.highlight;
        this.highlight = this.highlighter.handleMouse(mx, my, type, this.highlight);
        $(this.canvas).css("cursor", this.highlighter.cursor);
        if (orig !== this.highlight) {
          this.renderCanvas();
        }
        if (type === 'up') {
          return this.trigger("highlightChanged", this.highlightRelativeToCrop());
        }
      }
    };
    EditDocumentPageView.prototype.clearHighlight = function() {
      if (this.highlight != null) {
        this.highlight = null;
        return this.render();
      }
    };
    EditDocumentPageView.prototype.highlightRelativeToCrop = function() {
      var cx, cx1, cy, cy1, hx, hx1, hy, hy1, _ref, _ref2, _ref3, _ref4;
      if (!((_ref = this.page.transformations) != null ? (_ref2 = _ref.crop) != null ? _ref2.length : void 0 : void 0) > 0) {
        return this.highlight;
      }
      _ref3 = this.page.transformations.crop, cx = _ref3[0], cy = _ref3[1], cx1 = _ref3[2], cy1 = _ref3[3];
      _ref4 = this.highlight, hx = _ref4[0], hy = _ref4[1], hx1 = _ref4[2], hy1 = _ref4[3];
      return [hx - cx, hy - cy, Math.min(hx1 - cx, cx1), Math.min(hy1 - cy, cy1)];
    };
    EditDocumentPageView.prototype.setHighlightRelativeToCrop = function(crop) {
      var cx, cx1, cy, cy1, hx, hx1, hy, hy1, _ref;
      if (crop) {
        _ref = this.page.transformations.crop || [0, 0, 0, 0], cx = _ref[0], cy = _ref[1], cx1 = _ref[2], cy1 = _ref[3];
        hx = crop[0], hy = crop[1], hx1 = crop[2], hy1 = crop[3];
        return this.highlight = [hx + cx, hy + cy, hx1 + cx, hy1 + cy];
      }
    };
    return EditDocumentPageView;
  })();
  Cropper = (function() {
    Cropper.prototype.grabMargin = 4;
    function Cropper(foreground, background) {
      this.foreground = foreground != null ? foreground : "black";
      this.background = background != null ? background : "rgba(200, 200, 200, 0.5)";
      this.handleMouse = __bind(this.handleMouse, this);
      this.render = __bind(this.render, this);
    }
    Cropper.prototype.render = function(canvas, crop, cropping) {
      var ctx, h, m, w, x, x1, y, y1;
      ctx = canvas.getContext('2d');
      w = canvas.width;
      h = canvas.height;
      if (crop) {
        x = crop[0], y = crop[1], x1 = crop[2], y1 = crop[3];
        ctx.fillStyle = this.background;
        ctx.fillRect(0, 0, x, h);
        ctx.fillRect(x, 0, w - x, y);
        ctx.fillRect(x1, y, w - x1, h - y);
        ctx.fillRect(x, y1, x1 - x, h - y1);
        ctx.strokeStyle = this.foreground;
        ctx.lineWidth = 2;
        ctx.strokeRect(x, y, x1 - x, y1 - y);
        if (cropping) {
          m = this.grabMargin;
          ctx.strokeStyle = this.foreground;
          ctx.strokeRect(x - m, y - m, 2 * m, 2 * m);
          ctx.strokeRect(x + (x1 - x) / 2 - m, y - m, 2 * m, 2 * m);
          ctx.strokeRect(x1 - m, y - m, 2 * m, 2 * m);
          ctx.strokeRect(x - m, y + (y1 - y) / 2 - m, 2 * m, 2 * m);
          ctx.strokeRect(x1 - m, y + (y1 - y) / 2 - m, 2 * m, 2 * m);
          ctx.strokeRect(x - m, y1 - m, 2 * m, 2 * m);
          ctx.strokeRect(x + (x1 - x) / 2 - m, y1 - m, 2 * m, 2 * m);
          return ctx.strokeRect(x1 - m, y1 - m, 2 * m, 2 * m);
        }
      }
    };
    Cropper.prototype.handleMouse = function(mx, my, type, crop) {
      var cursor, d, directions, dx, dy, m, ox, ox1, oy, oy1, x, x1, y, y1, _ref, _ref2;
      directions = "";
      cursor = "";
      if (crop) {
        m = this.grabMargin * 2;
        x = crop[0], y = crop[1], x1 = crop[2], y1 = crop[3];
        if (((x - m) < mx && mx < (x1 + m)) && ((y - m) < my && my < (y1 + m))) {
          if (((y - m) < my && my < (y + m))) {
            directions += "n";
          } else if (((y1 - m) < my && my < (y1 + m))) {
            directions += "s";
          }
          if (((x1 - m) < mx && mx < (x1 + m))) {
            directions += "e";
          } else if (((x - m) < mx && mx < (x + m))) {
            directions += "w";
          }
          if (directions) {
            cursor = "" + directions + "-resize";
          } else {
            cursor = "move";
            directions = "+";
          }
        }
      }
      this.cursor = cursor || "crosshair";
      if (type === "down") {
        if (crop && !directions) {
          crop = [mx, my, mx, my];
        }
        this.mouseDownState = {
          x: mx,
          y: my,
          directions: directions,
          crop: ((function() {
            var _i, _len, _results;
            if (crop) {
              _results = [];
              for (_i = 0, _len = crop.length; _i < _len; _i++) {
                d = crop[_i];
                _results.push(d);
              }
              return _results;
            }
          })())
        };
      } else if (type === "up") {
        this.mouseDownState = {};
        if (crop) {
          x = crop[0], y = crop[1], x1 = crop[2], y1 = crop[3];
          if (x - x1 === 0 || y - y1 === 0) {
            return null;
          }
        }
      } else if (type === "move" && (((_ref = this.mouseDownState) != null ? _ref.x : void 0) != null)) {
        if (crop) {
          x = crop[0], y = crop[1], x1 = crop[2], y1 = crop[3];
        }
        if ("" === this.mouseDownState.directions) {
          x = this.mouseDownState.x;
          y = this.mouseDownState.y;
          x1 = mx;
          y1 = my;
        }
        if ("+" === this.mouseDownState.directions) {
          _ref2 = this.mouseDownState.crop, ox = _ref2[0], oy = _ref2[1], ox1 = _ref2[2], oy1 = _ref2[3];
          dx = mx - this.mouseDownState.x;
          dy = my - this.mouseDownState.y;
          x = ox + dx;
          y = oy + dy;
          x1 = ox1 + dx;
          y1 = oy1 + dy;
        }
        if (__indexOf.call(this.mouseDownState.directions, "w") >= 0) {
          x = mx;
        }
        if (__indexOf.call(this.mouseDownState.directions, "n") >= 0) {
          y = my;
        }
        if (__indexOf.call(this.mouseDownState.directions, "e") >= 0) {
          x1 = mx;
        }
        if (__indexOf.call(this.mouseDownState.directions, "s") >= 0) {
          y1 = my;
        }
        crop = [Math.min(x, x1), Math.min(y, y1), Math.max(x, x1), Math.max(y, y1)];
      }
      return crop;
    };
    return Cropper;
  })();
}).call(this);
