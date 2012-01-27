(function() {

  $('html').ajaxSend(function(event, xhr, settings) {
    if (!/^http:.*/.test(settings.url) || /^https:.*/.test(settings.url)) {
      return xhr.setRequestHeader("X-CSRFToken", $.cookie('csrftoken'));
    }
  });

  (function() {
    var date, days, months;
    months = ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"];
    days = ["Sunday", "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"];
    date = new Date();
    while (date.getDay() !== 1) {
      date = new Date(date.getTime() + (1000 * 60 * 60 * 24));
    }
    return $(".comment-maildate").html("" + days[date.getDay()] + ", " + (date.getDate()) + " " + months[date.getMonth()] + " " + (date.getFullYear()));
  })();

}).call(this);
