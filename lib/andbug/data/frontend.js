(function() {
  var crop_fjni, crop_jni, crop_pkg, last, layout_fjni, layout_frame, layout_jni, layout_slot, layout_slots, layout_thread, object_view, popout, popout_view, show_thread, value_view;
  var __slice = Array.prototype.slice;
  last = function(seq) {
    return seq[seq.length - 1];
  };
  crop_pkg = function(pkg) {
    var p;
    pkg = pkg.split(/\/|\./g);
    return ((function() {
      var _i, _len, _ref, _results;
      _ref = pkg.slice(0, -1);
      _results = [];
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        p = _ref[_i];
        _results.push(p[0]);
      }
      return _results;
    })()).join('.') + '.' + pkg[pkg.length - 1];
  };
  crop_jni = function(jni) {
    if (!jni) {
      return '';
    }
    switch (jni[0]) {
      case '[':
        return crop_jni(jni.slice(1)) + '[]';
      case 'L':
        return crop_pkg(jni.slice(1, -1));
      default:
        return jni;
    }
  };
  crop_fjni = function(fjni) {
    return crop_pkg(fjni.split('(')[0]);
  };
  crop_fjni = function(fjni) {
    var func, line;
    line = fjni.split(':')[1];
    func = crop_pkg(fjni.split('(')[0]);
    if (line) {
      return func + ':' + line;
    } else {
      return func;
    }
  };
  layout_fjni = function(fjni) {
    return $('<abbr>').text(crop_fjni(fjni)).attr('title', fjni);
  };
  layout_jni = function(jni) {
    return $('<abbr>').text(crop_jni(jni)).attr('title', jni);
  };
  object_view = function() {
    var div, jni, ref, slots;
    ref = arguments[0], jni = arguments[1], slots = 3 <= arguments.length ? __slice.call(arguments, 2) : [];
    div = $('<div>').append($('<h3>').append(layout_jni(jni)));
    if (slots.length) {
      div.append(layout_slots(slots));
    }
    return div;
  };
  value_view = function(ref, data) {
    return $('<span class="val">').text(data);
  };
  popout = function(c) {
    var p;
    p = $('<div class="popout">').append(c);
    return $('#container').append(p);
  };
  popout_view = function(ref, data) {
    var view;
    view = (function() {
      switch (data[0]) {
        case 'obj':
          return object_view.apply(null, [ref].concat(__slice.call(data.slice(1))));
        default:
          return value_view.apply(null, [ref].concat(__slice.call(data.slice(1))));
      }
    })();
    return popout(view);
  };
  layout_slot = function(l, base) {
    var key, ref, val;
    key = $('<span class="key">').text(l[0]);
    val = $('<span class="val">').text(l[1]);
    if (!base) {
      base = '';
    }
    ref = l[2];
    if (ref) {
      ref = base + ref;
      val = $('<a>').append(val);
      val.click(function() {
        return $.get(ref).success(function(data) {
          return popout_view(ref, data);
        });
      });
    }
    return $('<div class="slot">').append(key).append("=").append(val);
  };
  layout_slots = function(s, base) {
    var l, slots, _i, _len;
    slots = $('<div class="slots">');
    for (_i = 0, _len = s.length; _i < _len; _i++) {
      l = s[_i];
      slots.append(layout_slot(l, base));
    }
    return slots;
  };
  layout_frame = function(f) {
    var div;
    div = $('<div class="frame">').append($('<h3>').append(layout_fjni(f[0])));
    if (f[1]) {
      div.addClass('native');
    }
    if (f.length > 2) {
      div.append(layout_slots(f.slice(2)));
    }
    return div;
  };
  layout_thread = function(t) {
    var div, f, _i, _len, _ref;
    div = $('<div class="thread">');
    div.append($('<h3>').text("Thread: " + t[0]));
    _ref = t.slice(1);
    for (_i = 0, _len = _ref.length; _i < _len; _i++) {
      f = _ref[_i];
      div.append(layout_frame(f));
    }
    return div;
  };
  show_thread = function(t) {
    console.log(t);
    $('.frame').hide();
    return t.find('.frame').show();
  };
  $(function() {
    var t, threads, _i, _len;
    threads = eval($('#forest').text());
    for (_i = 0, _len = threads.length; _i < _len; _i++) {
      t = threads[_i];
      $('#threads').append(layout_thread(t));
    }
    show_thread($('#threads').children().first());
    $('.thread > h3').click(function(evt) {
      return show_thread($(this).parent());
    });
    return $('.thread > h3').mouseenter(function(evt) {
      return show_thread($(this).parent());
    });
  });
}).call(this);
