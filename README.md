# canna-recommend
Recommend cannabis strains and products to users, because there are thousands of strains and not enough time to learn about them all.
[Here's a video overview of the app.](https://youtu.be/3ZUYT7WfBL4)

# Docker build
This has 2 Docker builds for deployment.  One is the leafly.com scraper, and the other is the website app.  They are in progress, and don't fully work yet.

## leafly scraper
First, `cd leafly`, then run `docker build -t scrape-leafly .`.  This will build the docker image for the scraper.  To run the scraper docker image, do `docker run scrape-leafly`.


## debugging/interactive Docker shell
If you want to run the Docker image and do some debugging (e.g. for the scraper or server), you can run `docker run -it scrape-leafly /bin/bash`.  This will open up the bash.  It doesn't have ipython installed, so to run ipython for debugging you'd need to do `pip install ipython` once you were in the Docker container shell.

## Docker with GUI apps for debugging
It's helpful when scraping to have the GUI for debugging.  Using this command:
`docker run -it --net=host --env="DISPLAY" --volume="$HOME/.Xauthority:/root/.Xauthority:rw" scrape-leafly /bin/bash`
Reference: https://medium.com/@SaravSun/running-gui-applications-inside-docker-containers-83d65c0db110
Another idea that didn't seem to work: http://somatorio.org/en/post/running-gui-apps-with-docker/


# Old directions before docker upgrade:

# Directions for deployment
Install nltk packages:
```python
import nltk
for i in ['stopwords', 'wordnet']:
  nltk.download(i)
```
[Install mongodb](https://docs.mongodb.com/v3.2/tutorial/install-mongodb-on-ubuntu/) -- use the `install_mongodb.sh` file.
First, import the database:

```bash
cd leafly/leafly_mongodb.db
ulimit -n 64000
mongorestore -d leafly_backup_2016-11-01 leafly_backup_2016-11-01
```

Annoyingly, I had to change my `/etc/mongod.conf` file to have `bind_ip = 0.0.0.0` (http://stackoverflow.com/questions/24899849/connection-refused-to-mongodb-errno-111).

If you get an error, you may need to up the ulimit: http://stackoverflow.com/questions/34666769/mongodb-error-failed-24-too-many-open-files-using-pymongo


(The db was exported with `mongodump -d leafly_backup_2016-11-01 leafly_backup_2016-11-01`)
Make sure to run all scripts from the main directory of the project (canna-recommend).  E.g. python2 apps/web_app/app.py
This is due to relative imports in the script, which I standardized by expecting the script to be run from the home dir.

# Redirecting the port
To redirect the port you use (10001 here) to 80 (standard browser port it accesses), do:
`sudo iptables -t nat -A OUTPUT -o lo -p tcp --dport 80 -j REDIRECT --to-port 10001`
http://askubuntu.com/questions/444729/redirect-port-80-to-8080-and-make-it-work-on-local-machine
add it to /etc/rc.local to make it persistent on restarts:
`sudo nano /etc/rc.local`

# Scraping analytical360
To scrape this site, I created a postgresql database (`CREATE DATABASE arch360;` from within psql),
then created some tables:

```bash
psql arch360
```

```sql

```

# Spinning up AWS, etc

IMPORTANT: the `post_main_addr` variable in apps/web_app/static/js/app.js needs to be updated to the elastic ip for the server!

To be able to access the site, we have to make available port 80:  Enter the commands
`sudo iptables -A INPUT -i eth0 -p tcp --dport 80 -j ACCEPT`
`sudo iptables -A INPUT -i eth0 -p tcp --dport 10001 -j ACCEPT`
`sudo iptables -A PREROUTING -t nat -i eth0 -p tcp --dport 80 -j REDIRECT --to-port 10001`

-- this one seemed to the the final key to making it work, after running the above 3
`sudo iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-ports 10001`

#### not sure if these are necessary
`sudo iptables -t nat -D PREROUTING 1`
`sudo iptables -t nat -A OUTPUT -o lo -p tcp --dport 80 -j REDIRECT --to-port 10001`

You will have to redirect the port to port 80 (standard for browsers): `sudo iptables -t nat -A PREROUTING -p tcp --dport 80 -j REDIRECT --to-ports 10001` (https://gist.github.com/kentbrew/776580), may also need to do `sudo iptables -t nat -D PREROUTING 1`
`sudo iptables -t nat -A OUTPUT -o lo -p tcp --dport 80 -j REDIRECT --to-port 10001`
Could possibly put in here:
`sudo nano /etc/rc.local`

You might have to run `sudo service mongod start` after starting the instance.  Check to make sure mongo is working with `service mongo status`.


I got a domain name on namecheap for less than $10 for a year.  Then, I followed [this tutorial](http://techgenix.com/namecheap-aws-ec2-linux/) to get the address forwarding to the AWS instance.  You do not need the period after the DNS server names.

Clone the repo, and go to the main directory.  Open up a tmux shell (`tmux new -s server`).  `ctrl+b`, then `d` to exit the session.  `tmux attach -t server` to get back in.  Run `python apps/web_app/app.py` and it should startup.

# Phone blues

debugging android from chrome:  visit this address in chrome `chrome://inspect/#devices` (http://stackoverflow.com/questions/32473199/inspect-devices-is-not-shown-in-chrome)

# Cleaning up
To tidy up the app code, I used [js-beautify](https://github.com/beautify-web/js-beautify).
`pip install jsbeautifier`
`js-beautify main2.html --type "html" -o main.html`
`js-beautify js/app.js --type "js" -o js/app.js`
`js-beautify css/app.css --type "css" -o css/app.css`

For python scripts I used autopep8: `autopep8 file.py --in-place`

There is a script called `clean_all.py` which can be run to clean all python files and web files.
