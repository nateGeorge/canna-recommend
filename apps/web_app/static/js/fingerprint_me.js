// this fingerprints devices for personalization/tracking/analysis

function post(data, loc, check) {
    if (check == false) {
      $.ajax({
              url: 'http://' + window.location.host + loc,
              type: 'POST',
              data: JSON.stringify(data),
              contentType: 'application/json',
              success: function(data) {
                  console.log('post success!')
                  check = true;
              },
              error: function(jqXHR, textStatus, err) {
                  console.log('post error');
              }
        });
    }
}

function getIP() {
  // gets IP address, duh
  $.getJSON('//gd.geobytes.com/GetCityDetails?callback=?', function(geo_data) {
    // jsondata = JSON.stringify(data, null, 2)
    // console.log(jsondata);
    console.log(geo_data["geobytesipaddress"]);
    data.ip = geo_data["geobytesipaddress"];
    // post({ip: data["geobytesipaddress"]}, '/ip', sent_ip);
  });

}

var sent_id = false; // for checking if id has been sent to server
var cookie_id = 'cannadviseme_test';
var fp; // the fingerprint from browser info
var jscook; // cookie thru js
var options = {extendedFontList: true};
var data = {}; // for storing ID stuff for tracking/posting to server
new Fingerprint2(options).get(function(result){
  fp = result[0];
  dataDict = result[1];
  console.log('id from fingerprintjs2:');
  console.log(fp);
  console.log(dataDict);
  jscook = Cookies.get(cookie_id);
  console.log('cookie:', jscook);
  data.js_cookie = jscook;
  // post(data, '/reg_cookie', sent_cook);
  data.fingerprint = fp;
  getIP();
  if (jscook === undefined) {
    Cookies.set(cookie_id, fp, { exires: 1000000000, path: '/' });
  }
  post(data, '/fingerprint', sent_id);
  // post(dataDict, '/datadict', sent_dd);
});
