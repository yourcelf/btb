global.window = require('jsdom').jsdom().createWindow()
require('../vendor/jquery.min.js').jQuery # injects into window.
global.$ = window.$
global._ = require('underscore')
global.Backbone = require('../vendor/backbone-min.js')
require('../moderation/common.coffee')
btb = window.btb

describe "strToDate", ->
  it 'should work for a variety of dates', ->
    dates =
      "2011-11-11T11:11:11": [new Date(2011, 10, 11, 11, 11, 11), "2011-11-11"]
      "2012-01-11T11:11:11": [new Date(2012, 0, 11, 11, 11, 11), "2012-1-11"]
      # Tricky octal bug.
      "2011-08-04T13:42:04": [new Date(2011, 7, 4, 13, 42, 4), "2011-8-4"]

    for src, [date, formatted] of dates
      toDate = btb.strToDate src
      expect(toDate).toEqual date
      expect(btb.formatDate toDate).toEqual formatted
