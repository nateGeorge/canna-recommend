var post_main_addr = 'http://localhost:10001'; // address with flask api
var json;

// Upload photo
function uploadSuccess(r) {
    hideSpinner();
    json = r.response;
    drawBoxes();
    console.log("Code = " + r.responseCode);
    console.log("Response = " + r.response);
    console.log("Sent = " + r.bytesSent);
}

function uploadFail(evt) {
    hideSpinner();
    alert('Something went wrong. Check you are connected to the internet.')
    console.log(evt.target.error.code);
}

function upload(data) {
    showSpinner();
    var options = new FileUploadOptions();
    options.fileKey = "image";
    options.mimeType = "image/jpeg";
    var ft = new FileTransfer();
    ft.upload(data, encodeURI('http://api.pyimagesearch.com/face_detection/detect/'), uploadSuccess, uploadFail, options);
};

// Draw output
function drawBoxes() {

    if (json === undefined) return;

    var data = JSON.parse(json);
    if (!data.success || data.faces.length === 0) {
        alert('No faces found');
        return;
    }

    // original dimensions
    var nwidth = document.getElementById('image').naturalWidth;
    var nheight = document.getElementById('image').naturalHeight;

    // scaled dimensions
    var width = $('#image').width();
    var height = $('#image').height();

    // adjust for center-block class on image
    var ml = $('#image').css('marginLeft');
    var _left = +ml.replace('px', '');
    var mt = $('#image').css('marginTop');
    var _top = +mt.replace('px', '');

    data.faces.forEach(function (face) {

        var x0 = face[0];
        var y0 = face[1];
        var x1 = face[2];
        var y1 = face[3];

        var _x0 = (width / nwidth * x0 + _left).toFixed(0);
        var _y0 = (height / nheight * y0 + _top).toFixed(0);
        var _x1 = (width / nwidth * x1 + _left).toFixed(0) - _x0;
        var _y1 = (height / nheight * y1 + _top).toFixed(0) - _y0;

        console.info('style=\'left: '
            + _x0 + 'px; top: '
            + _y0 + 'px; width: '
            + _x1 + 'px; height: '
            + _y1 + 'px\'');

        jQuery('<div id=\'box\' style=\'left: '
            + _x0 + 'px; top: '
            + _y0 + 'px; width: '
            + _x1 + 'px; height: '
            + _y1 + 'px\' class=\'box img-responsive\'></div>', {
            }).appendTo('#wrapper');

    });
};

window.onload = drawBoxes;
window.onresize = drawBoxes;

// Capture photo
function photoSuccess(imageData) {

    // Remove any existing boxes
    $('.box').remove();

    // Display the image
    $('#image').attr("src", imageData);

    // Let's identify faces
    upload(imageData);
}

function photoFail(message) {
    alert('Failed because: ' + message);
}

function takePhoto() {
    navigator.camera.getPicture(photoSuccess, photoFail, { quality: 50, destinationType: Camera.DestinationType.FILE_URI });
}

function showSpinner() {
    $('#camera').fadeOut(function () {
        $('#spinner').fadeIn();
    });
}

function hideSpinner() {
    $('#spinner').fadeOut(function () {
        $('#camera').fadeIn();
    });
}

$('#camera').click(function () {
    // Hide welcome page
    $('#landing').fadeOut(function () {
        // Take a picture
        takePhoto();
    });
});

// http://stackoverflow.com/questions/6630772/javascript-pop-from-object
var ObjectStack = function(obj) {
    this.object = obj;
    this.stack=[];
};

ObjectStack.prototype.pop = function() {
    var key = this.stack.pop();
    var prop = this.object[key];
    delete this.object[key];
    return prop;
};

// http://stackoverflow.com/questions/12987719/javascript-how-to-randomly-sample-items-without-replacement
function getRandomFromBucket() {
   var randomIndex = Math.floor(Math.random()*bucket.length);
   return bucket.splice(randomIndex, 1)[0];
}

var bucket;
function getRandomElements(lest, n=3) {
  // takes in a list and returns n random elements
  // without replacement
  bucket = [];
  var returnlest = [];

  for (var i=0; i<=lest.length - 1; i++) {
      bucket.push(i);
  }

  for (var i=0; i<=n; i++) {
      returnlest.push(lest[getRandomFromBucket()]);
  }

  return returnlest;

}

// load words for making recommendation when that section has loaded
var words, rows, categories, rand;
$(words).ready(function () {
  $.post(post_main_addr + '/get_product_words', function (data, err) {
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
      // first choose a category to pull words from
      // http://stackoverflow.com/questions/9071573/is-there-a-simple-way-to-make-a-random-selection-from-an-array-in-javascript-or
      // rand = Math.random();
      // rand *= num_cats;
      // rand = Math.floor(rand);
      // console.log(rand);
      rows = $(v).children();
      //var cur_cat = categories.pop(rand);
      rows[0].innerHTML = cats[i];
      word_samp = getRandomElements(words[cats[i]]);
      rows.slice(1).each(function(i, e) {
        e.innerHTML = word_samp[i];
      });
  });
}

// when the words are clicked, toggle their active state
$('.list-group-item').click(function() {
    if ($(this).hasClass('active')) {
      $(this).removeClass('active');
    } else {
      $(this).addClass('active');
    }
});


function recommend(words) {
  // $.ajax({
  //   url: post_main_addr + '/send_words',
  //   data: JSON.stringify({'words':words}),
  //   type: 'POST',
  //   contentType: 'application/json',
  //   dataType: 'json',
  //   success: function(response) {
  //       console.log(response);
  //   },
  //   error: function(error) {
  //       console.log(error);
  //   }
  // });
  // $.post(post_main_addr + '/send_words', data={'words':words}, function (data, err) {
  //   if (err) {console.log(err);}
  //   console.log(data);
  // });
  $.post(post_main_addr + '/send_words', data={ 'word_list' : words }, function (data, err) {
    console.log(data);
  });
  // var data = {
  //     screening: '1',
  //     assistance: 'wheelchair access',
  //     guests: [
  //         {
  //             first: 'John',
  //             last: 'Smith'
  //         },
  //         {
  //             first: 'Dave',
  //             last: 'Smith'
  //         }
  //     ]
  // };
  //
  // $.ajax({
  //     type: 'POST',
  //     url: post_main_addr + '/send_words',
  //     data: JSON.stringify(data),
  //     dataType: 'json',
  //     contentType: 'application/json; charset=utf-8'
  // }).done(function(msg) {
  //     alert("Data Saved: " + msg);
  // });
}

$('#recommend').click(function () {
    // Hide welcome page
    $('#landing').fadeOut(function () {
        // make recommendation
        var words = [];
        $('.list-group-item').each(function(i, v) {
          if ($(v).hasClass('active')) {
            var text = v.innerHTML;
            console.log(text);
            words.push(text);
          }
        });
        recommend(words);
    });
});
