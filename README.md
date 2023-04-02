# cfdns-update

Cloudflare DDNS Updater in Python

**Please Note**: I'm not planning on updating this container any longer. Its functionality has been merged into another tool I built that handles DDNS updates for Cloudflare, DNS Made Easy, or DNS-O-Matic. You can find that one at [jcostom/ddnsup](https://github.com/jcostom/ddnsup).

Recently I stood up a new domain and moved a couple over to Cloudflare. With this move I wanted to do some DDNS updates via their API, much like I've been doing with with DNS Made Easy and the jcostom/dme-update container. This is pretty much a direct port of that to the Cloudflare API.

There's a sample docker-compose file included. If you like to roll on your own, for example...

```bash
docker run -d \
    --name=cfdns \
    --user 1000:1000 \
    --restart=unless-stopped \
    -v /var/docks/cfdns:/config \
    -e APITOKEN=24681357-abc3-12345-a1234-987654321 \
    -e ZONEID=123456 \
    -e RECORDS=host1,host2 \
    -e USETELEGRAM=1 \
    -e CHATID=0 \
    -e MYTOKEN=1111:1111-aaaa_bbbb.cccc \
    -e SITENAME='HOME' \
    -e TZ='America/New_York' \
    -e DEBUG=0 \
    jcostom/cfdns-update
```

If you decide to not use Telegram for notifications, set the USETELEGRAM variable to 0, and then you can leave out the CHATID, MYTOKEN, and SITENAME variables.

Creating a Telegram bot is fairly well documented at this point and is beyond the scope of this README. Have a read up on that, get your bot token, get your chat ID, and you're ready to roll.

Optionally, if you're having trouble, and want to do some debugging, set the DEBUG=1 variable. As of version 1.2, you can set the variable, and now that I've transitioned to the Python logging module, you get decent debug logging in the standard container log output. Just look at the regular output of `docker logs container-name`.
