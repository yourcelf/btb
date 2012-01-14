(function() {
  $('html').ajaxSend(function(event, xhr, settings) {
    if (!/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url)) {
      return xhr.setRequestHeader("X-CSRFToken", $.cookie('csrftoken'));
    }
  });
}).call(this);
