(function() {
  var __hasProp = Object.prototype.hasOwnProperty, __extends = function(child, parent) {
    for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; }
    function ctor() { this.constructor = child; }
    ctor.prototype = parent.prototype;
    child.prototype = new ctor;
    child.__super__ = parent.prototype;
    return child;
  }, __bind = function(fn, me){ return function(){ return fn.apply(me, arguments); }; };
  btb.Comment = (function() {
    __extends(Comment, Backbone.Model);
    function Comment() {
      Comment.__super__.constructor.apply(this, arguments);
    }
    return Comment;
  })();
  btb.CommentList = (function() {
    __extends(CommentList, Backbone.Collection);
    function CommentList() {
      CommentList.__super__.constructor.apply(this, arguments);
    }
    return CommentList;
  })();
  btb.Letter = (function() {
    __extends(Letter, Backbone.Model);
    function Letter() {
      this.url = __bind(this.url, this);
      Letter.__super__.constructor.apply(this, arguments);
    }
    Letter.prototype.url = function() {
      var baseUrl;
      baseUrl = btb.LetterList.prototype.baseUrl;
      if (this.get("id")) {
        return baseUrl + "/" + this.get("id");
      } else {
        return baseUrl;
      }
    };
    return Letter;
  })();
  btb.LetterList = (function() {
    __extends(LetterList, btb.FilteredPaginatedCollection);
    function LetterList() {
      LetterList.__super__.constructor.apply(this, arguments);
    }
    LetterList.prototype.model = btb.Letter;
    LetterList.prototype.baseUrl = "/correspondence/letters.json";
    LetterList.prototype.parse = function(response) {
      this.counts = response.counts;
      return LetterList.__super__.parse.call(this, response);
    };
    return LetterList;
  })();
  btb.Correspondence = (function() {
    __extends(Correspondence, Backbone.Model);
    function Correspondence() {
      Correspondence.__super__.constructor.apply(this, arguments);
    }
    return Correspondence;
  })();
  btb.CorrespondenceList = (function() {
    __extends(CorrespondenceList, btb.FilteredPaginatedCollection);
    function CorrespondenceList() {
      CorrespondenceList.__super__.constructor.apply(this, arguments);
    }
    CorrespondenceList.prototype.model = btb.Correspondence;
    CorrespondenceList.prototype.baseUrl = "/correspondence/correspondence.json";
    return CorrespondenceList;
  })();
  btb.Mailing = (function() {
    __extends(Mailing, Backbone.Model);
    function Mailing() {
      this.url = __bind(this.url, this);
      Mailing.__super__.constructor.apply(this, arguments);
    }
    Mailing.prototype.url = function() {
      var baseUrl;
      baseUrl = btb.MailingList.prototype.baseUrl;
      if (this.get("id")) {
        return baseUrl + "/" + this.get("id");
      } else {
        return baseUrl;
      }
    };
    return Mailing;
  })();
  btb.MailingList = (function() {
    __extends(MailingList, btb.FilteredPaginatedCollection);
    function MailingList() {
      MailingList.__super__.constructor.apply(this, arguments);
    }
    MailingList.prototype.model = btb.Mailing;
    MailingList.prototype.baseUrl = "/correspondence/mailings.json";
    return MailingList;
  })();
  btb.NeededLetters = (function() {
    __extends(NeededLetters, Backbone.Model);
    function NeededLetters() {
      this.url = __bind(this.url, this);
      NeededLetters.__super__.constructor.apply(this, arguments);
    }
    NeededLetters.prototype.url = function() {
      var base;
      base = "/correspondence/needed_letters.json";
      if (this.get("consent_form_cutoff")) {
        return base + "?" + $.param({
          consent_form_cutoff: this.get("consent_form_cutoff")
        });
      }
      return base;
    };
    return NeededLetters;
  })();
  btb.LetterAddingMenu = (function() {
    __extends(LetterAddingMenu, Backbone.View);
    function LetterAddingMenu() {
      this.addLetter = __bind(this.addLetter, this);
      this.hideLoading = __bind(this.hideLoading, this);
      this.showLoading = __bind(this.showLoading, this);
      this.render = __bind(this.render, this);
      LetterAddingMenu.__super__.constructor.apply(this, arguments);
    }
    LetterAddingMenu.prototype.template = _.template($("#letterMenu").html());
    LetterAddingMenu.prototype.events = {
      'change select.type-chooser': 'addLetter'
    };
    LetterAddingMenu.prototype.initialize = function(options) {
      if (options == null) {
        options = {};
      }
      return this.recipient = options.recipient;
    };
    LetterAddingMenu.prototype.render = function() {
      return $(this.el).html(this.template({
        recipient: this.recipient.toJSON()
      }));
    };
    LetterAddingMenu.prototype.showLoading = function() {
      return $(".loading", this.el).show();
    };
    LetterAddingMenu.prototype.hideLoading = function() {
      return $(".loading", this.el).hide();
    };
    LetterAddingMenu.prototype.addLetter = function(event) {
      var letter, type;
      this.showLoading();
      type = $(event.currentTarget).val();
      letter = new btb.Letter({
        recipient: this.recipient.toJSON(),
        org_id: $(".org_id", this.el).val(),
        type: type
      });
      if (type === "letter") {
        $(".org-chooser", this.el).hide();
        return this.trigger("editLetter", letter);
      } else if (type !== "") {
        return letter.save({}, {
          success: __bind(function(model, response) {
            this.hideLoading();
            this.render();
            return this.trigger("letterAdded", model);
          }, this)
        });
      }
    };
    return LetterAddingMenu;
  })();
  btb.LetterEditor = (function() {
    __extends(LetterEditor, Backbone.View);
    function LetterEditor() {
      this.enqueue = __bind(this.enqueue, this);
      this.renderOrgs = __bind(this.renderOrgs, this);
      this.render = __bind(this.render, this);
      this.hideLoading = __bind(this.hideLoading, this);
      this.showLoading = __bind(this.showLoading, this);
      this.cancel = __bind(this.cancel, this);
      LetterEditor.__super__.constructor.apply(this, arguments);
    }
    LetterEditor.prototype.template = _.template($("#letterEditor").html());
    LetterEditor.prototype.orgTemplate = _.template($("#letterOrgChooser").html());
    LetterEditor.prototype.events = {
      'click .enqueue-letter': 'enqueue',
      'click .cancel': 'cancel'
    };
    LetterEditor.prototype.initialize = function(options) {
      var recipient, _ref;
      if (options == null) {
        options = {};
      }
      this.letter = options.letter;
      if (!((_ref = this.letter.get("recipient")) != null ? _ref.organizations : void 0)) {
        recipient = new btb.User({
          id: this.letter.get("recipient_id")
        });
        recipient.fetch({
          success: __bind(function(model) {
            this.letter.set({
              recipient: model
            });
            return this.renderOrgs();
          }, this),
          error: __bind(function() {
            return alert("Server error " + (recpient.url()));
          }, this)
        });
      }
      return this;
    };
    LetterEditor.prototype.cancel = function() {
      return this.trigger("cancelled");
    };
    LetterEditor.prototype.showLoading = function() {
      return $(".loading", this.el).show();
    };
    LetterEditor.prototype.hideLoading = function() {
      return $(".loading", this.el).hide();
    };
    LetterEditor.prototype.render = function() {
      $(this.el).html(this.template({
        letter: this.letter.toJSON()
      }));
      this.renderOrgs();
      return this;
    };
    LetterEditor.prototype.renderOrgs = function() {
      return $(".org-chooser", this.el).html(this.orgTemplate({
        letter: this.letter.toJSON()
      }));
    };
    LetterEditor.prototype.enqueue = function() {
      this.showLoading();
      this.letter.set({
        body: $(".letter-body", this.el).val(),
        org_id: $(".org_id", this.el).val(),
        send_anonymously: !$(".not-anonymous", this.el).is(":checked")
      });
      return this.letter.save({}, {
        success: __bind(function(model, response) {
          this.hideLoading();
          this.trigger("letterAdded", model);
          this.type = "";
          this.letter = null;
          return $(".custom-letter").remove();
        }, this),
        error: __bind(function(model, response) {
          $(".letter-error", this.el).html(_.escapeHTML(response.responseText)).addClass("error");
          return alert("Server error " + (this.letter.url()));
        }, this)
      });
    };
    return LetterEditor;
  })();
  btb.CommentsMailingTable = (function() {
    __extends(CommentsMailingTable, Backbone.View);
    function CommentsMailingTable() {
      this.render = __bind(this.render, this);
      CommentsMailingTable.__super__.constructor.apply(this, arguments);
    }
    CommentsMailingTable.prototype.heading = _.template($("#commentHeading").html());
    CommentsMailingTable.prototype.template = _.template($("#commentRow").html());
    CommentsMailingTable.prototype.initialize = function(options) {
      if (options.modelParams) {
        return this.collection = new btb.CommentList(_.map(options.modelParams, function(c) {
          return new btb.Comment(c);
        }));
      } else {
        return this.collection = new btb.CommentList;
      }
    };
    CommentsMailingTable.prototype.render = function() {
      var comment, _i, _len, _ref;
      $(this.el).html(this.heading());
      _ref = this.collection.models;
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        comment = _ref[_i];
        $(this.el).append(this.template({
          comment: comment.toJSON()
        }));
      }
      return this;
    };
    return CommentsMailingTable;
  })();
  btb.LetterRow = (function() {
    __extends(LetterRow, Backbone.View);
    function LetterRow() {
      this.render = __bind(this.render, this);
      this.hideLoading = __bind(this.hideLoading, this);
      this.showLoading = __bind(this.showLoading, this);
      this.specialHandling = __bind(this.specialHandling, this);
      this.deleteLetter = __bind(this.deleteLetter, this);
      this.markLetterUnsent = __bind(this.markLetterUnsent, this);
      this.markLetterSent = __bind(this.markLetterSent, this);
      this.resendLetter = __bind(this.resendLetter, this);
      this.editLetter = __bind(this.editLetter, this);
      LetterRow.__super__.constructor.apply(this, arguments);
    }
    LetterRow.prototype.template = _.template($("#letterRow").html());
    LetterRow.prototype.specialHandlingTemplate = _.template($("#specialHandlingDialog").html());
    LetterRow.prototype.events = {
      'click .edit-letter': 'editLetter',
      'click .resend-letter': 'resendLetter',
      'click .delete-letter': 'deleteLetter',
      'click .mark-letter-sent': 'markLetterSent',
      'click .mark-letter-unsent': 'markLetterUnsent',
      'click .special-handling': 'specialHandling'
    };
    LetterRow.prototype.initialize = function(letter) {
      return this.letter = letter;
    };
    LetterRow.prototype.editLetter = function(event) {
      return this.trigger("editLetter", this.letter);
    };
    LetterRow.prototype.resendLetter = function(event) {
      var copy;
      this.showLoading();
      copy = this.letter.clone();
      return copy.save({
        "id": null,
        "sent": null,
        "created": void 0
      }, {
        success: __bind(function(model) {
          this.hideLoading();
          return this.trigger("letterAdded", model);
        }, this),
        error: __bind(function() {
          return alert("Server error " + (copy.url()));
        }, this)
      });
    };
    LetterRow.prototype.markLetterSent = function(event) {
      this.showLoading();
      return this.letter.save({
        "sent": true
      }, {
        success: __bind(function(model) {
          this.hideLoading();
          this.trigger("letterChanged", model);
          return this.render();
        }, this),
        error: __bind(function() {
          return alert("Server error " + (this.letter.url()));
        }, this)
      });
    };
    LetterRow.prototype.markLetterUnsent = function(event) {
      this.showLoading();
      return this.letter.save({
        "sent": null
      }, {
        success: __bind(function(model) {
          this.hideLoading();
          this.trigger("letterChanged", model);
          return this.render();
        }, this),
        error: __bind(function() {
          return alert("Server error " + (this.letter.url()));
        }, this)
      });
    };
    LetterRow.prototype.deleteLetter = function(event) {
      this.showLoading();
      return this.letter.destroy({
        success: __bind(function() {
          this.hideLoading();
          return this.trigger("letterDeleted", this.letter);
        }, this),
        error: __bind(function() {
          return alert("Server error " + (this.letter.url()));
        }, this)
      });
    };
    LetterRow.prototype.specialHandling = function(event) {
      var div;
      div = this.specialHandlingTemplate({
        letter: this.letter.toJSON()
      });
      return $(div).dialog({
        modal: true,
        width: 500,
        height: 300,
        title: "Special mail handling instructions"
      });
    };
    LetterRow.prototype.showLoading = function() {
      $(".not-loading", this.el).hide();
      return $(".loading", this.el).show();
    };
    LetterRow.prototype.hideLoading = function() {
      $(".not-loading", this.el).show();
      return $(".loading", this.el).hide();
    };
    LetterRow.prototype.render = function() {
      var commentsTable, _ref;
      $(this.el).html(this.template({
        letter: this.letter.toJSON(),
        commaddress: (_ref = this.letter.get("org")) != null ? _ref.mailing_address.replace(/\n/g, ", ") : void 0
      }));
      if (this.letter.get("type") === "comments") {
        commentsTable = new btb.CommentsMailingTable({
          modelParams: this.letter.get("comments")
        });
        $(".comments-table", this.el).html(commentsTable.render().el);
      }
      return this;
    };
    return LetterRow;
  })();
  btb.CorrespondenceScanRow = (function() {
    __extends(CorrespondenceScanRow, Backbone.View);
    function CorrespondenceScanRow() {
      this.render = __bind(this.render, this);
      CorrespondenceScanRow.__super__.constructor.apply(this, arguments);
    }
    CorrespondenceScanRow.prototype.template = _.template($("#correspondenceScanRow").html());
    CorrespondenceScanRow.prototype.initialize = function(scan) {
      return this.scan = scan;
    };
    CorrespondenceScanRow.prototype.render = function() {
      $(this.el).html(this.template({
        scan: this.scan.toJSON()
      }));
      return this;
    };
    return CorrespondenceScanRow;
  })();
  btb.LetterTable = (function() {
    __extends(LetterTable, btb.PaginatedView);
    function LetterTable() {
      this.turnPage = __bind(this.turnPage, this);
      this.fetchItems = __bind(this.fetchItems, this);
      this.addPaginationRow = __bind(this.addPaginationRow, this);
      this.hideLoading = __bind(this.hideLoading, this);
      this.showLoading = __bind(this.showLoading, this);
      this.render = __bind(this.render, this);
      LetterTable.__super__.constructor.apply(this, arguments);
    }
    LetterTable.prototype.template = _.template($("#letterTableHeading").html());
    LetterTable.prototype.events = {
      'click span.pagelink': 'turnPage'
    };
    LetterTable.prototype.initialize = function(options) {
      if (options == null) {
        options = {
          filter: {}
        };
      }
      this.collection = new btb.LetterList;
      return this.collection.filter = options.filter;
    };
    LetterTable.prototype.render = function() {
      var letter, row, _i, _len, _ref;
      $(this.el).html(this.template());
      _ref = this.collection.models;
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        letter = _ref[_i];
        row = new btb.LetterRow(letter);
        row.bind("editLetter", __bind(function(letter) {
          return this.trigger("editLetter", letter);
        }, this));
        row.bind("letterDeleted", __bind(function(letter) {
          return this.fetchItems();
        }, this));
        $(this.el).append(row.render().el);
      }
      this.addPaginationRow(true, true);
      $(this.el).addClass("letter-table");
      return this;
    };
    LetterTable.prototype.showLoading = function() {
      return $(".fetch-loading", this.el).show();
    };
    LetterTable.prototype.hideLoading = function() {
      return $(".fetch-loading", this.el).hide();
    };
    LetterTable.prototype.addPaginationRow = function(bottom, top) {
      var pag;
      if (bottom == null) {
        bottom = true;
      }
      if (top == null) {
        top = false;
      }
      if (this.collection.length === 0) {
        $(this.el).append("<div class='row'>No results</div>");
      } else if (this.collection.pagination != null) {
        if (bottom) {
          pag = $("<div class='pagination'></div>");
          $(this.el).append(pag);
          this.renderPagination(this.collection, pag);
        }
        if (top) {
          pag = $("<div class='pagination'></div>");
          $(this.el).prepend(pag);
          this.renderPagination(this.collection, pag);
        }
      }
      return this;
    };
    LetterTable.prototype.fetchItems = function() {
      this.showLoading();
      return this.collection.fetch({
        success: __bind(function() {
          this.hideLoading();
          this.trigger("lettersFetched");
          return this.render();
        }, this),
        error: __bind(function() {
          return alert("Server errror " + (this.collection.url()));
        }, this)
      });
    };
    LetterTable.prototype.turnPage = function(event) {
      this.collection.filter.page = this.newPageFromEvent(event);
      this.setPageLoading();
      return this.collection.fetch({
        success: __bind(function() {
          return this.render();
        }, this),
        error: __bind(function() {
          return alert("Server error " + (this.collection.url()));
        }, this)
      });
    };
    return LetterTable;
  })();
  btb.CorrespondenceTable = (function() {
    __extends(CorrespondenceTable, btb.LetterTable);
    function CorrespondenceTable() {
      this.render = __bind(this.render, this);
      CorrespondenceTable.__super__.constructor.apply(this, arguments);
    }
    CorrespondenceTable.prototype.initialize = function(options) {
      if (options == null) {
        options = {
          filter: {}
        };
      }
      this.collection = new btb.CorrespondenceList;
      return this.collection.filter = options.filter;
    };
    CorrespondenceTable.prototype.render = function() {
      $(this.el).html(this.template());
      this.collection.each(__bind(function(obj) {
        var event, row, _i, _len, _ref;
        if (obj.get("letter") != null) {
          row = new btb.LetterRow(new btb.Letter(obj.get("letter")));
          _ref = ["letterAdded", "letterDeleted"];
          for (_i = 0, _len = _ref.length; _i < _len; _i++) {
            event = _ref[_i];
            row.bind(event, __bind(function(model) {
              return this.fetchItems();
            }, this));
          }
          row.bind("editLetter", __bind(function(letter) {
            return this.trigger("editLetter", letter);
          }, this));
        } else if (obj.get("scan") != null) {
          row = new btb.CorrespondenceScanRow(new btb.Scan(obj.get("scan")));
        }
        return $(this.el).append(row.render().el);
      }, this));
      this.addPaginationRow();
      $(this.el).addClass("letter-table");
      return this;
    };
    return CorrespondenceTable;
  })();
  btb.CorrespondenceManager = (function() {
    __extends(CorrespondenceManager, Backbone.View);
    function CorrespondenceManager() {
      this.editLetter = __bind(this.editLetter, this);
      this.render = __bind(this.render, this);
      CorrespondenceManager.__super__.constructor.apply(this, arguments);
    }
    CorrespondenceManager.prototype.initialize = function(options) {
      this.recipient = options.recipient;
      this.table = new btb.CorrespondenceTable({
        filter: {
          user_id: this.recipient.id,
          per_page: 5
        }
      });
      this.table.bind("editLetter", __bind(function(letter) {
        return this.editLetter(letter);
      }, this));
      this.table.fetchItems();
      this.adder = new btb.LetterAddingMenu({
        recipient: this.recipient
      });
      this.adder.bind("letterAdded", __bind(function(letter) {
        return this.table.fetchItems();
      }, this));
      this.adder.bind("editLetter", __bind(function(letter) {
        return this.editLetter(letter);
      }, this));
      $(this.el).html(this.adder.el);
      $(this.el).append(this.table.el);
      return this.render();
    };
    CorrespondenceManager.prototype.render = function() {
      this.adder.render();
      this.table.render();
      return this;
    };
    CorrespondenceManager.prototype.editLetter = function(letter) {
      var editor;
      editor = new btb.LetterEditor({
        letter: letter,
        orgs: this.userOrgs
      });
      $(this.adder.el).append(editor.render().el);
      editor.bind("cancelled", __bind(function() {
        return this.adder.render();
      }, this));
      return editor.bind("letterAdded", __bind(function(letter) {
        this.adder.render();
        return this.table.fetchItems();
      }, this));
    };
    return CorrespondenceManager;
  })();
  btb.MailingBuilder = (function() {
    __extends(MailingBuilder, Backbone.View);
    function MailingBuilder() {
      this.buildMailing = __bind(this.buildMailing, this);
      this.updateCounts = __bind(this.updateCounts, this);
      this.hideLoading = __bind(this.hideLoading, this);
      this.showLoading = __bind(this.showLoading, this);
      this.render = __bind(this.render, this);
      this.fetchItems = __bind(this.fetchItems, this);
      this.setCutoff = __bind(this.setCutoff, this);
      this.getCutoff = __bind(this.getCutoff, this);
      MailingBuilder.__super__.constructor.apply(this, arguments);
    }
    MailingBuilder.prototype.template = _.template($("#buildMailing").html());
    MailingBuilder.prototype.events = {
      'change .consent-form-cutoff': 'fetchItems',
      'change .filters input[type=checkbox]': 'updateCounts',
      'click input[name=build_mailing]': 'buildMailing'
    };
    MailingBuilder.prototype.initialize = function() {
      this.needed = new btb.NeededLetters;
      return this.fetchItems();
    };
    MailingBuilder.prototype.getCutoff = function() {
      return $(".consent-form-cutoff", this.el).val();
    };
    MailingBuilder.prototype.setCutoff = function(val) {
      return $(".consent-form-cutoff", this.el).val(val);
    };
    MailingBuilder.prototype.fetchItems = function() {
      $(this.el).show();
      this.showLoading();
      this.needed.set({
        "consent_form_cutoff": this.getCutoff() || void 0
      });
      return this.needed.fetch({
        success: __bind(function(model) {
          this.needed = model;
          this.hideLoading();
          return this.updateCounts();
        }, this),
        error: __bind(function() {
          return alert("Server error " + (this.needed.url()));
        }, this)
      });
    };
    MailingBuilder.prototype.render = function() {
      $(this.el).html(this.template());
      $(".consent-form-cutoff", this.el).datepicker({
        dateFormat: 'yy-mm-dd'
      });
      return this;
    };
    MailingBuilder.prototype.showLoading = function() {
      return $(".loading", this.el).show();
    };
    MailingBuilder.prototype.hideLoading = function() {
      return $(".loading", this.el).hide();
    };
    MailingBuilder.prototype.updateCounts = function() {
      var count, counts, name, possible, total;
      counts = this.needed.toJSON();
      total = 0;
      possible = 0;
      $(".choice", this.el).hide();
      for (name in counts) {
        count = counts[name];
        count = parseInt(count);
        if (count > 0) {
          $(".choice." + name, this.el).show();
          $(".choice." + name + " .count", this.el).html(_.escapeHTML(count));
          if ($("input[name=" + name + "]", this.el).is(":checked")) {
            total += count;
          }
          possible += count;
        }
      }
      $(".total-count", this.el).html(total);
      if (possible === 0) {
        $(this.el).hide();
      }
      if (total === 0) {
        $("input[name=build_mailing]", this.el).attr("disabled", "disabled");
      } else {
        $("input[name=build_mailing]", this.el).removeAttr("disabled");
      }
      if (this.getCutoff()) {
        return $(".choice.consent_form", this.el).show();
      }
    };
    MailingBuilder.prototype.buildMailing = function() {
      var cutoff, input, mailing, types, _i, _len, _ref;
      types = [];
      cutoff = this.getCutoff();
      _ref = $("input[type=checkbox]:checked", this.el);
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        input = _ref[_i];
        types.push($(input).attr("name"));
      }
      mailing = new btb.Mailing;
      this.showLoading();
      return mailing.save({
        types: types,
        consent_cutoff: cutoff
      }, {
        success: __bind(function(model) {
          this.hideLoading();
          this.setCutoff("");
          this.trigger("mailingAdded", model);
          return this.fetchItems();
        }, this),
        error: __bind(function() {
          return alert("Server errror " + (mailing.url()));
        }, this)
      });
    };
    return MailingBuilder;
  })();
  btb.LetterFilter = (function() {
    __extends(LetterFilter, Backbone.View);
    function LetterFilter() {
      this.updateCounts = __bind(this.updateCounts, this);
      this.chooseSearch = __bind(this.chooseSearch, this);
      this.chooseType = __bind(this.chooseType, this);
      this.render = __bind(this.render, this);
      this.hideLoading = __bind(this.hideLoading, this);
      this.showLoading = __bind(this.showLoading, this);
      LetterFilter.__super__.constructor.apply(this, arguments);
    }
    LetterFilter.prototype.template = _.template($("#letterFilters").html());
    LetterFilter.prototype.events = {
      'change input[type=checkbox]': 'chooseType',
      'keyup  input[type=text]': 'chooseSearch'
    };
    LetterFilter.prototype.initialize = function() {
      return this.filter = {};
    };
    LetterFilter.prototype.showLoading = function() {
      return $("input[type=text]", this.el).addClass("loading");
    };
    LetterFilter.prototype.hideLoading = function() {
      return $("input[type=text]", this.el).removeClass("loading");
    };
    LetterFilter.prototype.render = function() {
      $(this.el).html(this.template());
      return this;
    };
    LetterFilter.prototype.chooseType = function() {
      var input, types, _i, _len, _ref;
      types = [];
      _ref = $(".filters input:checked[type=checkbox]", this.el);
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        input = _ref[_i];
        types.push($(input).attr("name"));
      }
      this.filter.types = types.join(",");
      return this.trigger("filterChanged", this.filter);
    };
    LetterFilter.prototype.chooseSearch = function() {
      var txt;
      txt = $("input[type=text]", this.el).val();
      if (!txt && (this.filter.text != null)) {
        delete this.filter.text;
      }
      this.filter.text = txt;
      return this.trigger("filterChanged", this.filter);
    };
    LetterFilter.prototype.updateCounts = function(counts) {
      var count, name, _results;
      $(".choice", this.el).hide();
      _results = [];
      for (name in counts) {
        count = counts[name];
        name = name || "other";
        _results.push(count > 0 ? ($("span." + name + " .count", this.el).html(_.escapeHTML(count)), $(".choice." + name, this.el).show()) : void 0);
      }
      return _results;
    };
    return LetterFilter;
  })();
  btb.MailingFilter = (function() {
    __extends(MailingFilter, btb.PaginatedView);
    function MailingFilter() {
      this.chooseItem = __bind(this.chooseItem, this);
      this.chooseAllUnsent = __bind(this.chooseAllUnsent, this);
      this.chooseAllSent = __bind(this.chooseAllSent, this);
      this.chooseAll = __bind(this.chooseAll, this);
      this.chooseEnqueued = __bind(this.chooseEnqueued, this);
      this.deselect = __bind(this.deselect, this);
      this.fetchItems = __bind(this.fetchItems, this);
      this.hideLoading = __bind(this.hideLoading, this);
      this.showLoading = __bind(this.showLoading, this);
      this.render = __bind(this.render, this);
      MailingFilter.__super__.constructor.apply(this, arguments);
    }
    MailingFilter.prototype.template = _.template($("#mailingFilters").html());
    MailingFilter.prototype.events = {
      'click .all': 'chooseAll',
      'click .all-sent': 'chooseAllSent',
      'click .all-unsent': 'chooseAllUnsent',
      'click .enqueued': 'chooseEnqueued'
    };
    MailingFilter.prototype.initialize = function() {
      this.collection = new btb.MailingList;
      return this.fetchItems();
    };
    MailingFilter.prototype.render = function() {
      var item, mailing, _i, _len, _ref;
      $(this.el).html(this.template());
      this.items = {};
      _ref = this.collection.models;
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        mailing = _ref[_i];
        item = new btb.MailingFilterItem(mailing);
        item.bind("itemSelected", this.chooseItem);
        item.bind("itemDeleted", __bind(function(item) {
          this.fetchItems();
          return this.trigger("itemDeleted", item);
        }, this));
        item.bind("itemChanged", this.chooseItem);
        $(".mailings", this.el).append(item.render().el);
        this.items[mailing.get("id")] = item;
      }
      return this;
    };
    MailingFilter.prototype.showLoading = function() {
      return $(".loading", this.el).show();
    };
    MailingFilter.prototype.hideLoading = function() {
      return $(".loading", this.el).hide();
    };
    MailingFilter.prototype.fetchItems = function() {
      this.showLoading();
      return this.collection.fetch({
        success: __bind(function() {
          this.render();
          this.trigger("mailingsLoaded");
          return this.hideLoading();
        }, this),
        error: __bind(function() {
          return alert("Server error " + (this.collection.url()));
        }, this)
      });
    };
    MailingFilter.prototype.deselect = function() {
      this.filter = {};
      return $("li", this.el).removeClass("selected");
    };
    MailingFilter.prototype.chooseEnqueued = function() {
      this.deselect();
      $("li.enqueued", this.el).addClass("selected");
      this.filter.mailing_id = null;
      this.filter.unsent = 1;
      this.trigger("filterChanged", this.filter);
      btb.app.navigate("#/mail");
      return this;
    };
    MailingFilter.prototype.chooseAll = function() {
      this.deselect();
      $("li.all", this.el).addClass("selected");
      this.trigger("filterChanged", this.filter);
      btb.app.navigate("#/mail/all");
      return this;
    };
    MailingFilter.prototype.chooseAllSent = function() {
      this.deselect();
      this.filter.sent = 1;
      $("li.all-sent", this.el).addClass("selected");
      this.trigger("filterChanged", this.filter);
      btb.app.navigate("#/mail/sent");
      return this;
    };
    MailingFilter.prototype.chooseAllUnsent = function() {
      this.deselect();
      $("li.all-unsent", this.el).addClass("selected");
      this.filter.unsent = 1;
      this.trigger("filterChanged", this.filter);
      btb.app.navigate("#/mail/unsent");
      return this;
    };
    MailingFilter.prototype.chooseItem = function(item) {
      if (!isNaN(item)) {
        item = this.items[item];
      }
      if (!item) {
        return this.chooseEnqueued();
      }
      this.deselect();
      $(item.el).addClass("selected");
      this.filter.mailing_id = item.mailing.get("id");
      this.trigger("filterChanged", this.filter);
      btb.app.navigate("#/mail/" + this.filter.mailing_id);
      return this;
    };
    return MailingFilter;
  })();
  btb.MailingFilterItem = (function() {
    __extends(MailingFilterItem, Backbone.View);
    function MailingFilterItem() {
      this.change = __bind(this.change, this);
      this.clearCache = __bind(this.clearCache, this);
      this.markUnsent = __bind(this.markUnsent, this);
      this.markSent = __bind(this.markSent, this);
      this.hideLoading = __bind(this.hideLoading, this);
      this.showLoading = __bind(this.showLoading, this);
      this.deleteItem = __bind(this.deleteItem, this);
      this.selectItem = __bind(this.selectItem, this);
      this.render = __bind(this.render, this);
      MailingFilterItem.__super__.constructor.apply(this, arguments);
    }
    MailingFilterItem.prototype.template = _.template($("#mailingFilterItem").html());
    MailingFilterItem.prototype.tagName = 'li';
    MailingFilterItem.prototype.events = {
      'click .item': 'selectItem',
      'click .delete': 'deleteItem',
      'click .mark-sent': 'markSent',
      'click .mark-unsent': 'markUnsent',
      'click .clear-cache': 'clearCache'
    };
    MailingFilterItem.prototype.initialize = function(mailing) {
      return this.mailing = mailing;
    };
    MailingFilterItem.prototype.render = function() {
      $(this.el).html(this.template({
        mailing: this.mailing.toJSON()
      }));
      if (this.mailing.get("date_finished")) {
        $(this.el).removeClass("unsent");
      } else {
        $(this.el).addClass("unsent");
      }
      return this;
    };
    MailingFilterItem.prototype.selectItem = function() {
      return this.trigger("itemSelected", this);
    };
    MailingFilterItem.prototype.deleteItem = function() {
      this.showLoading();
      return this.mailing.destroy({
        success: __bind(function() {
          this.hideLoading();
          return this.trigger("itemDeleted", this.mailing);
        }, this),
        error: __bind(function() {
          return alert("Server errror " + (this.mailing.url()));
        }, this)
      });
    };
    MailingFilterItem.prototype.showLoading = function() {
      $(".loading", this.el).show();
      return $(".not-loading", this.el).hide();
    };
    MailingFilterItem.prototype.hideLoading = function() {
      $(".loading", this.el).hide();
      return $(".not-loading", this.el).show();
    };
    MailingFilterItem.prototype.markSent = function() {
      return this.change({
        date_finished: true
      });
    };
    MailingFilterItem.prototype.markUnsent = function() {
      return this.change({
        date_finished: null
      });
    };
    MailingFilterItem.prototype.clearCache = function() {
      this.showLoading();
      return $.ajax({
        url: "/correspondence/clear_cache/" + this.mailing.get("id"),
        type: "POST",
        success: __bind(function() {
          return this.hideLoading();
        }, this),
        error: __bind(function(jqXHR, textStatus, errorThrown) {
          return alert("Server error: " + textStatus);
        }, this)
      });
    };
    MailingFilterItem.prototype.change = function(updates) {
      this.showLoading();
      return this.mailing.save(updates, {
        success: __bind(function(model) {
          this.mailing = model;
          this.trigger("itemChanged", this);
          return this.render();
        }, this)
      });
    };
    return MailingFilterItem;
  })();
  btb.OutgoingMailView = (function() {
    __extends(OutgoingMailView, Backbone.View);
    function OutgoingMailView() {
      this.delayedFetchLetters = __bind(this.delayedFetchLetters, this);
      this.fetchLetters = __bind(this.fetchLetters, this);
      this.render = __bind(this.render, this);
      this.editLetter = __bind(this.editLetter, this);
      OutgoingMailView.__super__.constructor.apply(this, arguments);
    }
    OutgoingMailView.prototype.template = _.template($("#outgoingMail").html());
    OutgoingMailView.prototype.initialize = function(path) {
      var navigateCallback;
      this.letters = new btb.LetterTable;
      this.letterFilter = new btb.LetterFilter;
      this.mailingFilter = new btb.MailingFilter;
      this.builder = new btb.MailingBuilder;
      this.letters.bind("editLetter", __bind(function(letter) {
        return this.editLetter(letter);
      }, this));
      this.letters.bind("lettersFetched", __bind(function() {
        this.letterFilter.updateCounts(this.letters.collection.counts);
        return this.letterFilter.hideLoading();
      }, this));
      this.letterFilter.bind("filterChanged", this.delayedFetchLetters);
      this.mailingFilter.bind("filterChanged", this.fetchLetters);
      this.mailingFilter.bind("itemDeleted", __bind(function() {
        this.fetchLetters();
        return this.builder.fetchItems();
      }, this));
      this.builder.bind("mailingAdded", __bind(function(mailing) {
        var goToNewOne;
        goToNewOne = __bind(function() {
          this.mailingFilter.chooseItem(mailing.get("id"));
          return this.mailingFilter.unbind("mailingsLoaded", goToNewOne);
        }, this);
        this.mailingFilter.bind("mailingsLoaded", goToNewOne);
        return this.mailingFilter.fetchItems();
      }, this));
      navigateCallback = __bind(function() {
        switch (path) {
          case "all":
            this.mailingFilter.chooseAll();
            break;
          case "sent":
            this.mailingFilter.chooseAllSent();
            break;
          case "unsent":
            this.mailingFilter.chooseAllUnsent();
            break;
          default:
            if (!isNaN(path)) {
              this.mailingFilter.chooseItem(parseInt(path));
            } else {
              this.mailingFilter.chooseEnqueued();
            }
        }
        return this.mailingFilter.unbind("mailingsLoaded", navigateCallback);
      }, this);
      this.mailingFilter.bind("mailingsLoaded", navigateCallback);
      return this;
    };
    OutgoingMailView.prototype.editLetter = function(letter) {
      var editor;
      editor = new btb.LetterEditor({
        letter: letter
      });
      editor.bind("letterAdded", __bind(function(letter) {
        return this.letters.fetchItems();
      }, this));
      editor.bind("cancelled", __bind(function() {
        return $(editor.el).remove();
      }, this));
      return $(this.letters.el).prepend(editor.render().el);
    };
    OutgoingMailView.prototype.render = function() {
      $(this.el).html(this.template());
      $(".letter-filter", this.el).html(this.letterFilter.render().el);
      $(".letters", this.el).html(this.letters.render().el);
      $(".mailing-filter", this.el).html(this.mailingFilter.render().el);
      $(".build-mailing", this.el).html(this.builder.render().el);
      return this;
    };
    OutgoingMailView.prototype.fetchLetters = function() {
      this.letterFilter.showLoading();
      this.letters.collection.filter = _.extend({}, this.letterFilter.filter, this.mailingFilter.filter);
      return this.letters.fetchItems();
    };
    OutgoingMailView.prototype.delayedFetchLetters = function() {
      this.letterFilter.showLoading();
      if (this._fetchLetterDelay != null) {
        clearTimeout(this._fetchLetterDelay);
      }
      return this._fetchLetterDelay = setTimeout(this.fetchLetters, 100);
    };
    return OutgoingMailView;
  })();
}).call(this);
