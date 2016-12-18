var post_main_addr = 'http://0.0.0.0:10001' // 'http://cannadvise.me' //'http://35.161.235.42:10001'; // address with flask api

function add_to_bag(word, i, rec) {
  var index = chosen_words.indexOf(word);
  if (index != -1 & rec != true) {console.log('already in chosen_words'); return;}
  get_chosen_words();
  // if it's already in the chosen words, return
  if (i) {
    vpos = 150 + i * 20;
  } else {
    vpos = 150 + chosen_words.length * 30;
  }
  // words on image from here: https://css-tricks.com/text-blocks-over-image/
  $('ul.bag').append(
  '<li class="bag_words"><h2 class="bag">'
    + word +
    '<span class="fa-stack fa-1x"> \
      <a> \
        <i class="fa fa-remove fa-stack-1x" style="color:green"></i> \
      </a> \
    </span> \
  </h2></li><br>')
  // delete element when click 'remove'
  $('.fa-remove').click(function () {
    // strip all whitespace
    var cur_word = $(this).parent().parent().parent().text().trim();
    $(this).parent().parent().parent().remove();
    // delete from chosen_words
    var index = chosen_words.indexOf(cur_word);
    chosen_words.splice(index, 1);
    // deactivate selected text if visible
    $('.list-group-item').each(function(i, v) {
      if ($(v).text() == cur_word) {
        $(v).removeClass('active');
      }
    });
  });
  $('ul.bag').width($('#bag_im').width()*1.3);
  $('#empty_bag').click(function() {
      chosen_words = [];
      empty_bag();
  });
}

function empty_bag() {
  $('.bag_words').each(function(i, v) {
    $(v).remove();
  });
  $('.list-group-item').each(function(i, v) {
    $(this).removeClass('active');
  })
}

function remove_from_bag(word) {
  $('.bag_words').each(function(i, v) {
    if ($(v).text().trim() == word.trim()) {
      $(v).remove();
    }
  });
}

function fit_bag() {
  var maxW = $(window).width();
  //$('#bag_im').css('width', maxW*0.9);
  console.log('resizing bag');
  $(chosen_words).each(function(i, v) {
    console.log(v);
    add_to_bag(v, i, rec=true);
  });
  // resize table in bag
  $('ul.bag').attr('top', $('#bag_im').height()*0.2);
}

function load_new_words() {
  // loads new choices of words and categories
  $.post(post_main_addr + '/get_product_words', function(data, err) {
      words = $.parseJSON(data);
      categories = Object.keys(words);
      var num_cats = categories.length;
      setWords();
  });
}

function load_main() {
    console.log('loading...');
    $('.main_page').load('./main.html', complete = function() {

        // when the words are clicked, toggle their active state
        $('.list-group-item').click(function() {
            if ($(this).hasClass('active')) {
                $(this).removeClass('active');
                remove_from_bag(this.innerHTML);
                var index = chosen_words.indexOf(this.innerHTML);
                chosen_words.splice(index, 1);
            } else {
                $(this).addClass('active');
                add_to_bag(this.innerHTML);
            }
        });

        $.post(post_main_addr + '/get_product_words', function(data, err) {
            words = $.parseJSON(data);
            categories = Object.keys(words);
            var num_cats = categories.length;
            setWords();
        });

        $('#refresh').click(function() {
            get_chosen_words();
            console.log(chosen_words);
            load_new_words();
        });

        // need to set this here, otherwise explore doesn't exist yet
        $('#explore').click(function() {
            console.log('exploring...');
            get_chosen_words();
            console.log(chosen_words);
            $('#landing').fadeOut(function() {
                // make recommendation
                $('.main_page').load('rec_body.html', complete = function() {
                    recommend(chosen_words);
                    $('#bag_im').ready(function() {
                      // fit im width to screen (for mobile)
                      console.log('bag ready');
                      fit_bag();
                    });
                });
            });
        });

        $('#bag_im').ready(function() {
          // fit im width to screen (for mobile)
          var maxW = $(window).width();
          //$('#bag_im').css('width', maxW*0.9);
          console.log('bag ready');
          $(chosen_words).each(function(i, v) {
            console.log(v);
            add_to_bag(v, i, true);
          });
          // scale table
          $('ul.bag').attr('top', $('#bag_im').height()*0.2);
        });

    }).hide().fadeIn(); // fade in the content
}

window.onload = load_main();
window.onresize = fit_bag();

// http://stackoverflow.com/questions/6630772/javascript-pop-from-object
var ObjectStack = function(obj) {
    this.object = obj;
    this.stack = [];
};

ObjectStack.prototype.pop = function() {
    var key = this.stack.pop();
    var prop = this.object[key];
    delete this.object[key];
    return prop;
};

// http://stackoverflow.com/questions/12987719/javascript-how-to-randomly-sample-items-without-replacement
function getRandomFromBucket() {
    var randomIndex = Math.floor(Math.random() * bucket.length);
    return bucket.splice(randomIndex, 1)[0];
}

var bucket;

function getRandomElements(lest, n) {
    // takes in a list and returns n random elements
    // without replacement
    if (n == undefined) {n=3;}
    bucket = [];
    var returnlest = [];

    for (var i = 0; i <= lest.length - 1; i++) {
        bucket.push(i);
    }

    if (n == 1) {
      // problem with indexing 1 I guess
      return lest[getRandomFromBucket()];
    }
    for (var i = 0; i <= n; i++) {
        returnlest.push(lest[getRandomFromBucket()]);
    }

    return returnlest;

}

// load words for making recommendation when that section has loaded
var words, rows, categories, rand;
$('#words').ready(function() {
    $.post(post_main_addr + '/get_product_words', function(data, err) {
        words = $.parseJSON(data);
        categories = Object.keys(words);
        var num_cats = categories.length;
        setWords();
    });
});

function setWords() {
    // sets words in the list groups
    cats = getRandomElements(categories, $('.list-group').length);
    $('.list-group').each(function(i, v) {
        rows = $(v).children();
        rows[0].innerHTML = cats[i];
        word_samp = getRandomElements(words[cats[i]]);
        rows.slice(1).each(function(i, e) {
            e.innerHTML = word_samp[i];
            if ($(e).hasClass('active')) {
              $(e).removeClass('active');
            }
        });
    }).hide().fadeIn();
}

var BASE_URL = 'https://www.leafly.com';

function recommend(chosen_words, callback) {
    $.post(post_main_addr + '/send_words', data = {
        word_list: chosen_words
    }, function(data, err) {
        console.log(data);
        data = JSON.parse(data)
        recs = data['recs'];
        var links = data['links'];
        $('.list-group-item').each(function(i, v) {
            $(v).text(recs[i]);
            $(v).attr('href', BASE_URL + links[i]);
            $(v).attr('target', 'blank');
            console.log(recs[i]);
        });
    });
    if (callback) {
        console.log('doing callback');
        callback(recs);
    }
}

var chosen_words = [],
    recs;

function get_chosen_words() {
    $('.list-group-item').each(function(i, v) {
        if ($(v).hasClass('active')) {
            var text = v.innerHTML;
            if (chosen_words.indexOf(text) == -1) {
              console.log(text);
              chosen_words.push(text);
            }
        }
    });
}

//force not to cache so we can update pages
$.ajaxSetup({
    // Disable caching of AJAX responses
    cache: false
});

function load_leafly() {
  $('#page_beef').fadeOut(function() {
    $('.main_page').load('leafly_form.html', complete = function() {
      var user_list = ['Chill_Panda', 'sweetbutter80', 'emanuel80', 'KindGodess420'];
      var user = getRandomElements(user_list, 1);
      $('#leafly_user_id').val(user);
        $('#explore').click(function() {
          user = $('#leafly_user_id').val()
          var cur_results = $('.strain_rec').length;
          $.post(post_main_addr + '/send_leafly_user', data = {
              user: user, k: cur_results + 10 // so we always get at least 10 results
          }, function(data, err) {
            jsonData = JSON.parse(data);
            recs = jsonData['recs'].slice(cur_results, cur_results + 10);
            links = jsonData['links'].slice(cur_results, cur_results + 10);
            console.log(recs);
            $(recs).each(function(i, v) {
              $('#recs_links').append('<li class="strain_rec"><a target="_blank" href="http://www.leafly.com' + links[i] + '">' + v + '</a></li>');
            });
          });
          // $.post(post_main_addr + , data = {
          //     user: user
          //     }, function(data, err) {
          //     json_resp = $.parseJSON(data);
          //     console.log(json_resp);
          //     recs = Object.keys(json_resp);
          // });
        });
    });
  });
}

// navigation actions

$('#home').click(function() {
    chosen_words = [];
    load_main();
});

$('#leafly_user').click(function() {
    chosen_words = [];
    load_leafly();
});

$('#science').click(function() {
    chosen_words = [];
    $('#page_beef').fadeOut(function() {
      $('.main_page').load('science.html', complete = function() {
      });
      });
});

$('#contact').click(function() {
    chosen_words = [];
    $('#page_beef').fadeOut(function() {
      $('.main_page').load('contact.html', complete = function() {
      });
    });
});

// for menu bar functionality
$(document).on('click','.navbar-collapse.in',function(e) {
    if( $(e.target).is('a') && $(e.target).attr('class') != 'dropdown-toggle' ) {
        $(this).collapse('hide');
    }
});

$(document).click(function (event) {
    var clickover = $(event.target);
    var $navbar = $(".navbar-collapse");
    var _opened = $navbar.hasClass("in");
    if (_opened === true && !clickover.hasClass("navbar-toggle")) {
        $navbar.collapse('hide');
    }
});
