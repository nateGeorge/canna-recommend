var chosen_words;
console.log('hey');
$('#products').ready(function() {
  chosen_words = JSON.parse(JSON.parse((window.name)));
  console.log(chosen_words);
  $('#products').text(chosen_words['recs']);
});
