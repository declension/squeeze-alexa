Troubleshooting
===============

Using the diagnostic tool
-------------------------
From your `squeezealexa` directory,
```bash
bin/local_test.py
```

This assumes you have Python. You can run this more explicitly (e.g. on Windows):

    python bin/local_test.py


**Update**: `local_test.py` can now diagnose _some_ common connection problems :smile:

This should connect with your settings as per `settings.py`. The latest diagnostics can help you find the root cause of many common connection / certificate problems (but not 100% accurate).
Some examples of how this can happen are included in the [tests](../tests/).


The skill is installed, but erroring when invoked
-------------------------------------------------

If everything is installed and the connectivity working, but your Echo is saying "there was a problem with your skill" or similar, try checking the [Cloudwatch logs](https://console.aws.amazon.com/cloudwatch/) (note there's a delay in getting the latest logs).
The squeeze-alexa logs are designed to be quite readable, and should help track down the problem.

If you think it's the speech, try using the test input page on the Amazon dev account portal.

If all else fails, raise an issue here...

### Strange IOErrors
If you're getting permission denied `IOErrors` reported in the logs,
make sure you cert file has world read (i.e. run `chmod 644 squeeze-alexa.pem`)

Checking certificate problems
-----------------------------

### Examine your local certificate
```bash
openssl x509 -in squeeze-alexa.pem -text -noout
```

If you just want to check the expiry date:
```bash
openssl x509 -in squeeze-alexa.pem -enddate -noout
```


Debugging SSL connection problems
---------------------------------

For `$MY_HOSTNAME` and `$MY_PORT` you can substitute your home IP / domain name (as used above). It also assumes your client cert is called `squeeze-alexa.pem`:

```bash
openssl s_client -connect $MY_HOSTNAME:$MY_PORT -cert squeeze-alexa.pem | openssl x509
```
Type <kbd>Ctrl</kbd><kbd>d</kbd> to exit.
If successful, this should give you a PEM-style certificate block with some info about your cert).

### That didn't work
OK let's try seeing the problem:
```bash
openssl s_client -connect $MY_HOSTNAME:$MY_PORT -cert squeeze-alexa.pem
```
Note especially towards the end, the _Verify return code_. This is very helpful getting to the bottom of connection problems.

### Connecting
For more debugging:
```bash
openssl s_client -connect $MY_HOSTNAME:$MY_PORT -quiet -cert squeeze-alexa.pem
```
Type `status`, and if a successful end-to-end connection is made you should see some gibberish that looks a bit like:
`...status   player_name%3AUpstairs...player_connected%3A1 player_ip%3A192.168.1...`

Checking your LMS CLI is actually working
-----------------------------------------

### Remotely
Assuming your LMS IP restrictions allow it (check the LMS GUI security settings), and that you are using the standard 9090 CLI port, you can normally telnet from your computer:

```bash
    telnet $LMS 9090
```
where `LMS` is the address of your Squeezebox server - usually this will be the same as `$MY_HOSTNAME` (though you might use the local name).
Then type `status`, or some other command, and see if you get an encoded response. If not, you **need** to fix this first.

### From your server
You can also try it directly on the LMS box if you think there's some networking problem. Use `netcat` (e.g. `opkg install netcat`) if you have it:

```bash
    echo "status" | netcat $LMS 9090
```

(and try `localhost` if that's not working. If still no joy, your DNS setup might be confused).

### Resilience / performance testing the SSL connection
For the hardcore amongst you, you can check performance (and that there are no TLS bugs / obvious holes):

```bash
openssl s_time -bugs -connect $MY_HOSTNAME:$MY_PORT -cert squeeze-alexa.pem -verify 4
```
