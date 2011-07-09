last = (seq) ->
    seq[seq.length - 1]

crop_pkg = (pkg) ->
    pkg = pkg.split(/\/|\./g)
    (p[0] for p in pkg[..-2]).join('.') + '.' + pkg[pkg.length - 1]

crop_jni = (jni) ->
    return '' if not jni
    switch jni[0]
        when '[' then crop_jni(jni[1..]) + '[]'
        when 'L' then crop_pkg(jni[1..-2]) 
        else jni

crop_fjni = (fjni) ->
    crop_pkg(fjni.split('(')[0])
    
crop_fjni = (fjni) ->
    line = fjni.split(':')[1]
    func = crop_pkg(fjni.split('(')[0])
    if line
        func + ':' + line
    else
        func

layout_fjni = (fjni) ->
    $('<abbr>').text(crop_fjni(fjni)).attr('title', fjni)

layout_jni = (jni) ->
    $('<abbr>').text(crop_jni(jni)).attr('title', jni)

sequence_view = (ref, jni, items ...) ->
    div = $('<div>').append(
        $('<h3>').append(layout_jni(jni))
    )
    div.append(layout_items(items, ref)) if items.length
    return div

object_view = (ref, jni, slots ...) ->
    div = $('<div>').append(
        $('<h3>').append(layout_jni(jni))
    )
    div.append(layout_slots(slots, ref)) if slots.length
    return div

value_view = (ref, data) ->
    $('<span class="val">').text(data)

popout = (c) ->
    p = $('<div class="popout">').append(c)
    $('#container').prepend(p)

popout_view = (ref, data) ->
    view = switch data[0]
           when 'obj'
               object_view(ref, data[1..] ...)
           when 'seq'
               sequence_view(ref, data[1..] ...)
           else
               value_view(ref, data[1..] ...)
    popout(view)

layout_value = (val, ref) ->
    val = $('<span class="val">').text(val)
    if ref
        console.log(ref)
        val = $('<a>').append(val)
        val.click -> $.get(ref).success (data) -> popout_view(ref, data)
    return val

layout_slot = (l, base) ->
    key = $('<span class="key">').text(l[0])
    val = $('<span class="val">').text(l[1])
    val = layout_value(l[1], base + l[2])
    return $('<div class="slot">').append(key).append("=").append(val)

layout_items = (items, base) ->
    if not base
        base = ''
    else if base.match(/[^\/]$/)
        base = base + '/'

    console.log(items)
    slots = $('<div class="slots">')
    sz = items.length
    for ix in [0 .. sz]
        slots.append(", ") if ix != 0
        slots.append(layout_value(items[ix], base + ix))
    return slots

layout_slots = (s, base) ->
    if not base
        base = ''
    else if base.match(/[^\/]$/)
        base = base + '/'

    slots = $('<div class="slots">')
    slots.append(layout_slot(l, base)) for l in s
    return slots

layout_frame = (f) ->
    div = $('<div class="frame">').append(
        $('<h3>').append(layout_fjni(f[0]))
    )
    div.addClass('native') if f[1]
    div.append(layout_slots f[2..]) if f.length > 2
    return div

layout_thread = (t) ->
    div = $('<div class="thread">')
    div.append($('<h3>').text("Thread: " + t[0]))
    div.append(layout_frame f) for f in t[1..]
    return div

show_thread = (t) ->
    console.log(t)
    $('.frame').hide()
    t.find('.frame').show()

$ -> 
    threads = eval($('#forest').text())    
    $('#threads').append(layout_thread t) for t in threads
    show_thread($('#threads').children().first())

    $('.thread > h3').click (evt) -> 
        show_thread($(this).parent())
        #$('.frame').hide()
        #$(this).parent().find('.frame').show()

    $('.thread > h3').mouseenter (evt) -> 
        show_thread($(this).parent())
