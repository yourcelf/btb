(function() {
  var __hasProp = Object.prototype.hasOwnProperty, __extends = function(child, parent) {
    for (var key in parent) { if (__hasProp.call(parent, key)) child[key] = parent[key]; }
    function ctor() { this.constructor = child; }
    ctor.prototype = parent.prototype;
    child.prototype = new ctor;
    child.__super__ = parent.prototype;
    return child;
  }, __bind = function(fn, me){ return function(){ return fn.apply(me, arguments); }; };
  btb.PendingScan = (function() {
    __extends(PendingScan, Backbone.Model);
    function PendingScan() {
      PendingScan.__super__.constructor.apply(this, arguments);
    }
    PendingScan.prototype.url = function() {
      var stub;
      stub = this.get("id") ? "/" + this.get("id") : "";
      return btb.PendingScanList.prototype.baseUrl + stub;
    };
    return PendingScan;
  })();
  btb.PendingScanList = (function() {
    __extends(PendingScanList, btb.FilteredPaginatedCollection);
    function PendingScanList() {
      PendingScanList.__super__.constructor.apply(this, arguments);
    }
    PendingScanList.prototype.model = btb.PendingScan;
    PendingScanList.prototype.baseUrl = "/scanning/pendingscans.json";
    PendingScanList.prototype.comparator = function(ps) {
      return -(new Date(ps.get("created")).getTime());
    };
    return PendingScanList;
  })();
  btb.PendingScans = (function() {
    __extends(PendingScans, btb.PaginatedView);
    function PendingScans() {
      this.showPending = __bind(this.showPending, this);
      this.showMissing = __bind(this.showMissing, this);
      this.turnPage = __bind(this.turnPage, this);
      this.pendingScanMissing = __bind(this.pendingScanMissing, this);
      this.removePendingScan = __bind(this.removePendingScan, this);
      this.fetchItems = __bind(this.fetchItems, this);
      this.renderItems = __bind(this.renderItems, this);
      this.render = __bind(this.render, this);
      PendingScans.__super__.constructor.apply(this, arguments);
    }
    PendingScans.prototype.template = _.template($("#pendingScanList").html());
    PendingScans.prototype.itemTemplate = _.template($("#pendingScanItem").html());
    PendingScans.prototype.events = {
      'click span.pagelink': 'turnPage',
      'click input.pending-scan-missing': 'pendingScanMissing',
      'click .remove-pending-scan': 'removePendingScan',
      'click .show-missing': 'showMissing',
      'click .show-pending': 'showPending'
    };
    PendingScans.prototype.initialize = function() {
      this.pendingScanList = new btb.PendingScanList;
      this.pendingScanList.filter.per_page = 6;
      return this.showPending();
    };
    PendingScans.prototype.render = function() {
      var userChooser;
      $(this.el).html(this.template({
        orgs: btb.ORGANIZATIONS
      }));
      userChooser = new btb.UserSearch;
      userChooser.bind("chosen", __bind(function(user) {
        return this.addPendingScan(user);
      }, this));
      $(".user-chooser-holder", this.el).html(userChooser.render().el);
      this.renderItems();
      return this;
    };
    PendingScans.prototype.renderItems = function() {
      $(".pending-scan-list .item", this.el).remove();
      if (this.pendingScanList.length === 0) {
        $(".pending-scan-list", this.el).hide();
      } else {
        $(".pending-scan-list", this.el).show();
      }
      this.pendingScanList.each(__bind(function(ps) {
        var author, rendered, row, uc;
        row = $(this.itemTemplate({
          pendingscan: ps.toJSON()
        }));
        rendered = $(".pending-scan-list", this.el).append(row);
        author = new btb.User(ps.get("author"));
        uc = new btb.UserCompact({
          user: author
        }).render().el;
        return $(".user-compact", row).html(uc);
      }, this));
      this.renderPagination(this.pendingScanList, $(".pagination", this.el));
      return this;
    };
    PendingScans.prototype.fetchItems = function() {
      return this.pendingScanList.fetch({
        success: __bind(function() {
          return this.renderItems();
        }, this)
      });
    };
    PendingScans.prototype.addPendingScan = function(user) {
      return this.pendingScanList.create({
        author_id: user.get("id"),
        org_id: $("[name=org_id]", this.el).val()
      }, {
        success: __bind(function(model) {
          return this.render();
        }, this)
      });
    };
    PendingScans.prototype.removePendingScan = function(event) {
      var ps;
      ps = this.pendingScanList.get(parseInt($("input.pending-scan-id", event.currentTarget).val()));
      this.pendingScanList.remove(ps);
      return ps.destroy({
        success: __bind(function() {
          return this.render();
        }, this)
      });
    };
    PendingScans.prototype.pendingScanMissing = function(event) {
      var gone, ps;
      ps = this.pendingScanList.get($(".pending-scan-id", $(event.currentTarget).parent()).val());
      gone = $(event.currentTarget).is(":checked");
      return ps.save({
        missing: gone ? 1 : 0
      }, {
        success: function(model) {},
        error: function() {
          return alert("Server error");
        }
      });
    };
    PendingScans.prototype.turnPage = function(event) {
      this.pendingScanList.filter.page = this.newPageFromEvent(event);
      this.setPageLoading();
      return this.fetchItems();
    };
    PendingScans.prototype.showMissing = function(event) {
      var psl;
      psl = this.pendingScanList;
      if (psl.filter.pending != null) {
        delete psl.filter.pending;
      }
      $(".show-pending", this.el).removeClass("chosen");
      psl.filter.missing = 1;
      $(".show-missing", this.el).addClass("chosen");
      return this.fetchItems();
    };
    PendingScans.prototype.showPending = function(event) {
      var psl;
      psl = this.pendingScanList;
      if (psl.filter.missing != null) {
        delete psl.filter.missing;
      }
      $(".show-missing", this.el).removeClass("chosen");
      psl.filter.pending = 1;
      $(".show-pending", this.el).addClass("chosen");
      return this.fetchItems();
    };
    return PendingScans;
  })();
}).call(this);
