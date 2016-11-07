$('#products').ready(function() {
    var chosen_words;
    chosen_words = JSON.parse(JSON.parse((window.name)));
    console.log(chosen_words);
    $('#products').text(chosen_words['recs']);
});