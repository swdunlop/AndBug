#!/usr/bin/env coffee

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

# TODO: edit out CSS elements to a stylesheet
# TODO: ensure these things are primitive type aware

complain = (problem) ->
    console.log(problem)
    alert(problem)
    #TODO: improvements needed

release_value = (doc, data) ->
    console.log("release", data)
    text = JSON.stringify(data)
    doc.data('data', data)
    doc.prop('contenteditable', false).text(text).css {
        'color':'', 'background-color':''
    }

submit_value = (doc) ->
    try
        new_data = $.parseJSON(doc.text())
    catch err
        return complain("could not parse #{new_data}: #{err}")
    old_data = doc.data('data')
    ref = doc.data('ref')

    # if old_data is new_data, let it go..
    return release_value(doc, old_data) if new_data == old_data
    
    #TODO: ensure type is consistent between new_data and old_data
    
    # indicate that we have started submitting..
    doc.css('color', 'red')
    req = post_json(doc.data('ref'), new_data)

    req.success (result) ->
        console.log(result)
        if result.error
            release_value(doc, old_data).css('color', 'red')
            complain(result.error)
        else
            release_value(doc, new_data).css('color', 'green')

    req.error (xhr, status, error) ->
        release_value(doc).text(old_data).css('color', 'red')
        complain(error || status)

    req.complete ->
        # after 3s, we clear the color
        after_timeout 3000, -> doc.css({'color':''})

# coffee-script hackers really prefer that funcs come last..
after_timeout = (ms, next) -> setTimeout(next, ms)

# $.post is json-stupid, so is bare $.ajax..
post_json = (url, data) ->
    $.ajax {
        type:'POST', dataType:'json'
        contentType:'application/json; charset=utf-8', 
        url : url, data : JSON.stringify(data)}

edit_value = (doc) -> 
    doc.text(JSON.stringify(doc.data('data')))
    doc.prop('contenteditable', true)
    doc.css('color', 'black').css('backgroundColor', 'white')
    doc.blur -> 
        doc.unbind('blur')  # blur tends to bounce..
        submit_value(doc)

value_view = (ref, data) ->
    doc = $('<span class="val">').text(data)
    doc.data('ref', ref).data('data', data)
    doc.click -> edit_value(doc)

#value_view = (ref, data) ->
#    $('<span class="val">').text(data)

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
