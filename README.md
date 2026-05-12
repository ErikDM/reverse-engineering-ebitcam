# Reverse engineering Ebitcam E3 (F300)

Products under the Ebitcam-name range from Wi-Fi and 4G/LTE outdoor security cameras to indoor IP and pan/tilt models and are sold through major e-commerce platforms such as Amazon and regional online retailers.
In 2021, I bought three Ebitcam IoT cameras from Amazon. The one that we are digging into today is the `Ebitcam E3 (F300)`, which has been sold at numerous occasions, ref https://www.amazon.co.uk/dp/B07WD872MQ. The camera has 1,003 global ratings so far, which indicates that it has been sold at a large scale.

<img width="387" height="473" alt="bilde" src="https://github.com/user-attachments/assets/6e78e11f-45f4-4d43-857a-0d0ab59ab469" />
<br>
<br>

Opening the camera shows the [UART](https://www.analog.com/en/resources/analog-dialogue/articles/uart-a-hardware-communication-protocol.html) ports quite clearly, as they are also labeled (not always the case for many IoT devices). They are labeled `GND (ground)`, `TX (transmit)`, and `RX (receive)` - which ultimately allows us to connect to both receive and transmit data back and forth to the device. Some vendors disable the `RX` port on the board, which will deny users connecting and sending commands to the device. Other vendors do not even terminate the UART pads, so you would have to dig even deeper. However, this is not the case here, as you can see in the picture below. This is what we call "easy mode".

<img width="588" height="602" alt="bilde" src="https://github.com/user-attachments/assets/81247e69-79be-4bd7-9f14-08f2cc608a79" />
<br>
<br>

The next step is connecting the device to a computer using a FTDI breakout board, or even a bus pirate. Depends what kind of hardware you have. I use a variety of hardware, but for this specific case I used my FTDI breakout USB to serial adapter. There are tons to choose from. Measuring the voltage on the UART pads shows that the board is `3.3 volt`. Some boards are `5 volt`, so keep this in mind before you connect your breakout board. I also measured the volate between `GND` and `RX/TX` after boot. It is worth meantioning that `TX` "flickers" during boot. You will see the pad dropping from `3.3 volt` on and off before it becomes stable. `RX` is usually quite stable and will not flicker the same way `TX` does. This is good to keep in mind if you come across unlabeled UART pads, which I do on a regular basis. The picture below shows my FTDI breakout board. You can buy something similar from for example [Sparkfun](https://www.sparkfun.com/sparkfun-ftdi-basic-breakout-3-3v.html).

<img width="380" height="380" alt="bilde" src="https://github.com/user-attachments/assets/54592ab5-d2d9-40e6-af1f-1371adfd4baa" />
<br>
<br>

Connecting the breakout board to the camera requires you to cross `RX` and `TX`, as shown below. `GND` connects to `GND`.

```
Camera TX  →  FTDI RX
Camera RX  ←  FTDI TX
Camera GND ↔  FTDI GND
```

<img width="931" height="334" alt="bilde" src="https://github.com/user-attachments/assets/51327384-9e16-4913-9416-a3bb2af5d4f9" />
<br>
<br>

I am using a probing kit to connect to the UART pads. Technically you could also solder them on, but I recommend using some sort of hardware to make your life easier connecting to these pads - especially if you are conducting a lot of hardware hacking. Connect to the camera with its power off.

<img width="647" height="454" alt="bilde" src="https://github.com/user-attachments/assets/523e5f76-40bb-4ae7-ba85-5ab67a8d993c" />

Before we can communicate with the device, we need to know the [baud rate](https://www.analog.com/en/resources/analog-dialogue/articles/uart-a-hardware-communication-protocol.html). This can be discovered using tools such as a logic analyser or an oscilloscope. However, many IoT cameras use the "default" `115200` baud rate. I have come across devices which use other than `115200`, but Ebitcam also uses this exact baud rate. You can use for example `PuTTY` (Windows) or `screen` (Linux) to connect to the device. Look at your device manager in Windows if you are unsure of which COM-port to use. Remember to use `Serial` in `PuTTY`.

<img width="450" height="435" alt="bilde" src="https://github.com/user-attachments/assets/2bef2c16-7821-438c-91a3-d3f792a353ed" />
<br>
<br>

After connecting using `PuTTY`, I powered on the device. Shortly after, we can see that the camera is trying to boot. Success! We can now see the console output.

<img width="851" height="806" alt="bilde" src="https://github.com/user-attachments/assets/952df695-7143-402c-8251-91026f4949cc" />
<br>
<br>

However, we are now prompted with a default login screen. Trying default credentials such as `root:root` and `root:admin` etc. did not work. I tried quite a lof of combinations, as I know from experience that many cameras use weak/default credentials. In some cases, no bypass is needed and you will land a root shell directly after boot. The next step is to bypass the login prompt.

<img width="743" height="218" alt="bilde" src="https://github.com/user-attachments/assets/4a97f98e-bd3f-4152-a3f7-d27c217cd81b" />
<br>
<br>

Not all cameras support cancelling the boot process and entering `u-boot`. However, this worked for this specific camera. Pressing `CTRL + C` during autoboot cancelled the initial boot process, which ultimately gave us access to `u-boot`. There are many things we can do from u-boot. Some tricks involves setting `bootargs` to `init=/bin/sh`. This will land you a root shell after boot. However, this did not work too well on this camera. 

<img width="1800" height="1200" alt="bilde" src="https://github.com/user-attachments/assets/da38dc34-69be-4766-a0f6-a90aa857ccc5" />
<br>
<br>

I wrote a Python script which connects to the FTDI breakout board on COM6 and uses `u-boot` to dump out the full firmware to a `.bin` file instead. `u-boot` can be used to read out the data from the firmware using the `sf` command. This was conducted in very small chunks at a time. Also, dumping firmware from UART can be quite unstable and unrealiable. Therefore, the Python script also checks if the data was written successfully (each block) before proceeding. If not, it will try to dump the data again. A former colleague of mine (Frode Hus) wrote a similar tool for Windows, which is called [RFDump](https://github.com/FrodeHus/RFDump). For this specific case, I wrote my own Python tool which has been added to this repository. The script sends the `CTRL + C` signal automatically and starts dumping.

<img width="973" height="380" alt="bilde" src="https://github.com/user-attachments/assets/7e3b302f-9107-4f05-853a-ce7baf00e4a3" />
<br>

<img width="973" height="424" alt="bilde" src="https://github.com/user-attachments/assets/463725e8-3f5e-442a-9ff9-97b2ddb32714" />
<br>

<img width="635" height="133" alt="bilde" src="https://github.com/user-attachments/assets/e6d9d561-2a2f-4d96-abc3-ffd4f8454cb1" />
<br>
<br>

After completing the dump, we are left with a `firmware.bin` file which we can reverse engineer to look inside the firmware - and ultimately bypassing the login prompt. `binwalk` can be used to extract the file system.

<img width="1623" height="349" alt="bilde" src="https://github.com/user-attachments/assets/06795bc9-2c00-4b57-91f2-2391d5a25df1" />
<br>
<br>

Shortly after, I discovered an `/etc/shadow` file which can be cracked. The `root` password used a weak hashing algorithm (DES), which allowed me to crack the password within 3 minutes and 31 seconds. However, this was NOT the password we were looking for and did not work for the device itself. The password might be used for other Ebitcam devices, but for now - we need to dig deeper to see how the root password is set/generated.

<img width="1490" height="1056" alt="bilde" src="https://github.com/user-attachments/assets/827384d3-ae25-4db9-a958-bc0b8b98829e" />
<br>
<br>

I have experienced in many cases the the root password is set randomly on each device, or even disabled/wiped. Some vendors do not like people poking around and logging into the device to discover vulnerabilities, mapping their infrastructure that the device is connected to and so forth. Many vendors go extreme measures to prevent users from reverse engineering, while others simply does not care. Looking through the file system after extracting it using `binwalk`, I discovered a file called `dev_passwd.sh`, which changes the device password. This is done after every reboot. So in practice, the root password will change every single time you reboot the camera. The password might seem random, but there is a pattern. The password is not as random as it seems...

Ultimately, the script uses the following values to generated the root password as a MD5 string and echoes it into the `chpasswd` command:

```
1. Device id (static)
2. CTX (random number value which changes after each boot)
3. pass.mp file (static for this device. Located under /mnt/mtd/ipc_data. Can also be found in the /tmp folder on the device itself)
4. pass.up file (static for this device. Located under /mnt/mtd/ipc_data. Can also be found in the /tmp folder on the device itself)
```

<img width="1276" height="598" alt="bilde" src="https://github.com/user-attachments/assets/1ba8239e-56a8-4568-8625-b8df40817e18" />
<br>
<br>

So where can we get the `CTX` value if it is generated randomly after boot? Well, it leaks itself in the hostname of the device after boot, along with the device id.

<img width="737" height="88" alt="bilde" src="https://github.com/user-attachments/assets/73204c7e-c009-4498-b4ef-0978afab3da1" />
<br>
<br>

With this information, we have all four values that we need to generate the root password ourselves and log into the device. I have created a Python script which can be used to generate the password automatically. Here we can enter all four values: `Device ID`, `CTX`, `pass.mp`, and `pass.up`. This generates a MD5 string which is the root password.

<img width="1628" height="217" alt="bilde" src="https://github.com/user-attachments/assets/a44a5743-8dc7-4417-80cb-a4fb2460370b" />
<br>
<br>

The password worked successfully for the `root` account.

<img width="1919" height="1028" alt="bilde" src="https://github.com/user-attachments/assets/16f91451-908c-4d05-a777-ee6e9b42a802" />
<br>

It is also worth mentioning that the password is stored in clear-text at `/tmp/pass.debug`.
<br>
<br>

# Digging deeper: "Call home" and remote access from vendor

Here is one of many examples regarding debugging features from vendor in the production firmware. The camera runs a webserver on port 80 by default. Here the user can log in and make minor adjustments to the certain configurations, such as hostname/device ID, Wi-Fi settings and so forth. The default password is `admin`.
<img width="1371" height="489" alt="bilde" src="https://github.com/user-attachments/assets/0a529aba-6522-4377-bace-11493706a3ec" />
<br>
<br>

However, I came across a debug page which has been left by the developers in order to debug and to create a Telnet backdoor on the device. The web path `http://device-ip/ccm/ccm_debug_m.js` is available and is not linked to any end-user feature. This was discovered by looking through the source code. Attempting to connect to this endpoint shows an `Invalid password` prompt and leaking a different CTX than the one for the operating system. I tried the password `test` and method `test` just to explore the endpoint to see if it could give me any useful information.

```
http://192.168.50.82/ccm/ccm_debug_m.js?hfrom_handle=1&dpassword=test&dmethod=test&dstart=0&dcounts=0&dsize=8048
```

<img width="1277" height="110" alt="bilde" src="https://github.com/user-attachments/assets/6cc1ed3b-8b00-4cb8-9d26-b21677924cc7" />
<br>
<br>

What if we use the same Python script as previously to generate a password for the web service as well? Obviously, the CTX for the webserver is `350087890`, while it is `7841` for the root pasword. We try to generate a password for the webserver using the same static values as previously, except for the `CTX`.

<img width="1729" height="110" alt="bilde" src="https://github.com/user-attachments/assets/4a9b1907-d1f6-4d47-97f4-c3cfedc5b2a0" />
<br>
<br>

We successfully managed to enter a remote debugging feature, which ultimately allows us to conduct memory dumps and even enable Telnet on a non-default port (method `telnet_on`).
<img width="1902" height="163" alt="bilde" src="https://github.com/user-attachments/assets/24daf0d6-b84a-47a3-aa4f-df13a95b8d80" />
<br>
<br>

Next, I tried using the `telnet_on` method, which was previously displayed. The request resulted in a 200 OK message, which indicates that Telnet has been enabled.

```
http://192.168.50.82/ccm/ccm_debug_m.js?hfrom_handle=1&dpassword=38de0bb5e3da5facbf70292b5811255e&dmethod=telnet_on&dstart=0&dcounts=0&dsize=8048
```

<img width="1530" height="115" alt="bilde" src="https://github.com/user-attachments/assets/c038accc-1cdc-4c1a-897e-2cfe0ee2cb57" />
<br>
<br>

Telnet is already running on localhost port 23 (internally), and is not accessible externally by other devices on the network. However, after enabling Telnet remotely on the webserver, we see that it is now listening on the non-default Telnet port on `9527`. This is ultimately a backdoor on the system for debugging purposes, hence the hidden `ccm_debug_m.js` webpage. The port is now exposed externally, and not internally such as port `23`.

<img width="1160" height="218" alt="bilde" src="https://github.com/user-attachments/assets/a9ff7e85-5acf-4a63-b6f9-3514a2e69cb4" />
<br>
<br>

I confirmed that it was possible to Telnet into the device using the newly enabled backdoor on port `9527`. 
<img width="884" height="802" alt="bilde" src="https://github.com/user-attachments/assets/5c7108e1-29d4-474c-a427-517a1f1d8233" />
<br>
<br>

Furthermore, I also noticed that the script `dump.sh` can be triggered from the web application using certain parameters, as shown below. This ultimately exposes information about the device. The passwords are hardcoded into the script as well:

```
wget -O ccm.dump "http://127.0.0.1/ccm/ccm_debug.js?hfrom_handle=201959&dpassword=debug_ccm&dmethod=dump&dargs__x_countz_=2&dargs=--type&dargs_1=all" (password: debug_ccm)
wget -O cgw.dump "http://127.0.0.1/ccm/ccm_debug.js?hfrom_handle=201959&dpassword=debug_gw&dmethod=cgw_dump&dargs__x_countz_=2&dargs=--type&dargs_1=all" (password: debug_gw)
wget -O mrmt.dump "http://127.0.0.1/ccm/ccm_debug.js?hfrom_handle=201959&dpassword=debug_gw&dmethod=mrmt_dump&dargs__x_countz_=2&dargs=--type&dargs_1=all" (password: debug_gw)
wget -O addr.dump "http://mipcm.com/cmipcgw/cmipcgw_get_req.js?hfrom_handle=379907&dclient=1&dclient_mode=&dclient_id="
```

<img width="1635" height="205" alt="bilde" src="https://github.com/user-attachments/assets/e7617622-9719-4b24-8bb7-3879c9730722" />
<br>
<br>

Visiting the three first pages does not give any information and seems not to work as intended.

<img width="1014" height="85" alt="bilde" src="https://github.com/user-attachments/assets/1fb7e150-99f4-40a6-a446-6ca161230974" />
<br>
<br>

However, I discovered another endpoint named `/ccm/ccm_debug_m.js`. This is almost identical with the previous `/ccm/ccm_debug.js` endpoint. Visiting the `/ccm/ccm_debug_m.js` endpoint exposes debug information about the device. The passwords are hardcoded into the firmware (`debug_gw` and `debug_ccm`).

<img width="1879" height="142" alt="bilde" src="https://github.com/user-attachments/assets/e9448e94-abbf-4fc0-a919-33fbffa9ffa1" />

<br>
<br>
<img width="1909" height="331" alt="bilde" src="https://github.com/user-attachments/assets/4b9b7183-d6da-4b36-a2e8-d588d8f27336" />

<br>
<br>

Notice the `method` parameter also in the requests. The `debug_gw` password works for the following methods:
```
cgw_dump
mrmt_dump
mhttp_dump
```
<br>


## Other "call home" and remote access features from vendor

The firmware contains multiple overlapping remote-control mechanisms from vendor. 

1. Hardcoded debug passwords shipped in firmware.
2. Hidden web debug tooling shipped in production content.
3. An always-on debug service started at boot.
4. Remote login/debug RPCs that respond without normal user authentication.
5. Vendor/cloud infrastructure endpoints baked into firmware config.
<br>

### 1. Hardcoded debug passwords

Firmware config includes static debug passwords in parentheses:

- `/project/apps/app/ipc/conf/20.50.00.00.ccm.conf:7 (debug_ccm)`
- `/project/apps/app/ipc/conf/00.00.00.00.cgw.conf:6 (debug_gw)`

Related config also contains a trace key:
- `/project/apps/app/ipc/conf/00.00.00.00.cgw.conf:2 (mining@24a8)`
<br>


### 2. Hidden production debug page (showed one example previously as well)

The firmware ships a hidden maintenance page:

- `/project/apps/app/ipc/data/http/__mining_test__.htm`

<img width="1296" height="233" alt="bilde" src="https://github.com/user-attachments/assets/16a9940e-865e-4c0b-a9e9-43330f0848bb" />

<br>

It loads a helper script that can manually issue low-level RPC messages:

- `/project/apps/app/ipc/data/http/scripts/test_v2.js`

That script contains templates for:

- `cacs_dh_req`
- `cacs_login_req`
- `ccm_debug_m`
- `ccm_test`

Relevant lines:

- `/project/apps/app/ipc/data/http/scripts/test_v2.js:247`
- `/project/apps/app/ipc/data/http/scripts/test_v2.js:261`
- `/project/apps/app/ipc/data/http/scripts/test_v2.js:278`
- `/project/apps/app/ipc/data/http/scripts/test_v2.js:290`
<br>


### 3. Debug service started automatically at boot

The boot scripts start an always-on debug service:

- `/ipc_project/apps/app/ipc/data/sh/dev_start.sh:260`
- `/project/apps/app/ipc/data/sh/dev_start.sh:260`

Command:

```
sh ./mipc_tool -cmd debug -server 1 &
```

This matches live device observations where `mipc_tool` listens on the debug port. Output from `mipc_tool`:
```
# mipc_tool -h
usage:
           -cmd crc32 -src src -dst dst
           -cmd crc8 -src src -dst dst
           -cmd pack_img_apply -pack pack_path
           -cmd pack_img_build -img img_path -pack pack_path
           -cmd pack_bin_build -file file_path -pack pack_path
           -cmd sign_verify -src src_file -sign sign_file
           -cmd pass -devid devid -refer refer -sp server_path -up user_path -plain plain -dst dst
           -cmd cmp -src src -dst dst
           -cmd debug -server 0/1 -ip ip -port port -file path . File content should be {pass:"pass",method:"telnet_on/telnet_off"}
           -cmd aac -op operate -src src -dst dst . op should be encode or decode
           -cmd disk seg xxx
           -cmd mtd -check xxx
           -cmd configure 
           -cmd wfc2  
           -cmd gpio_set -pin pin -value value
           -cmd gpio_get -pin pin
           -cmd 1375
           -cmd mboard_pin_set -pin pin -value value
           -cmd mboard_pin_get -pin pin -path path
           -cmd mboard_name_get -path path
           -cmd mboard_name_set -name name
           -cmd sn -sn_path sn_path -mac_path mac_path
           -cmd mvars [ -mod set|get ] [ -name name ] [ -value value ]
           -cmd wd [ -len len ]
           -cmd read_cfg [ -field xxx ] [ -cfg_file xxx ] [ -out_file xxx ]
           -cmd uart -mod write|read -name uart_name -baud baud_rate
           -cmd 4g -ppp on|off|status -at [AT command]
           -cmd tz 
           -cmd sh_msg -type type -name name -value value
           -cmd mboard_merge 
       -cmd json_parse -file filename -key key
       -cmd voice -path path_from_audio -name name_without_.aac
```
<br>


### 4. Telnet can be controlled by debug logic (as previously demonstrated)

Telnet enablement is wired into shipped shell scripts:

- `/ipc_project/apps/app/ipc/data/sh/dev_telnet.sh:44`
- `/project/apps/app/ipc/data/sh/dev_telnet.sh:44`

Command:

```
sh telnetd -p ${port} &
```

Related flag file:

- `/ipc_project/apps/app/ipc/data/default/file_rw_ctl_table:14`
<br>


### 5. Vendor infrastructure endpoints are baked into config

Signal/debug servers are shipped in firmware:

- `/ipc_data/server.xml:25`
- `/ipc_data/server.xml:26`
- `/ipc_data/server.json:1`

Representative values:

- `binnet://37.187.159.39:4001`
- `http://37.187.159.39:4080/ccm`
- `telnet://37.187.159.39:4024`

Live device netstat showed active outbound connections to:

- `37.187.159.39:4001`
- `37.187.159.39:4024`

<img width="1268" height="678" alt="bilde" src="https://github.com/user-attachments/assets/3e7049db-6612-4dfd-ac64-57c7c85469ce" />
<br>
<br>

Process list:
```
# ps 
  PID USER       VSZ STAT COMMAND
    1 root      1352 S    {squashfs_init} /gm/bin/busybox ash /squashfs_init
    2 root         0 SW   [kthreadd]
    3 root         0 SW   [ksoftirqd/0]
    4 root         0 SW   [kworker/0:0]
    5 root         0 SW   [kworker/u:0]
    6 root         0 SW<  [khelper]
    7 root         0 SW   [kdevtmpfs]
    8 root         0 SW<  [netns]
    9 root         0 DW   [FMEM_IDLE]
   10 root         0 SW   [sync_supers]
   11 root         0 SW   [bdi-default]
   12 root         0 SW<  [kblockd]
   13 root         0 SW   [khubd]
   14 root         0 SW<  [rpciod]
   15 root         0 SW   [kworker/0:1]
   16 root         0 SW   [khungtaskd]
   17 root         0 SW   [kswapd0]
   18 root         0 SWN  [ksmd]
   19 root         0 SW   [fsnotify_mark]
   20 root         0 SW<  [nfsiod]
   21 root         0 SW<  [ftspi020.0]
   22 root         0 SW   [kworker/u:1]
   23 root         0 SW   [mtdblock0]
   24 root         0 SW   [mtdblock1]
   25 root         0 SW   [mtdblock2]
   26 root         0 SW   [mtdblock3]
   27 root         0 SW   [mtdblock4]
   28 root         0 SW   [mtdblock5]
   31 root         0 SW   [kworker/u:2]
   32 root         0 SW   [kworker/0:2]
   57 root      1352 S    {linuxrc} init
   70 root         0 SWN  [jffs2_gcd_mtd3]
  137 root         0 SW   [flush-mtd-unmap]
 1243 root         0 SW<  [log_thread]
 1244 root         0 SWN  [threadmon]
 1245 root         0 SW<  [log_notify]
 1250 root         0 DW<  [gm_cache_extend]
 1254 root         0 DW<  [em_callback]
 1255 root         0 DW<  [em_putjob]
 1256 root         0 SW<  [osg_callback]
 1257 root         0 SW   [ivs_callback]
 1269 root         0 DW   [saradc thread]
 1293 root         0 DW   [isp_ae]
 1294 root         0 DW   [isp_awb]
 1295 root         0 DW   [isp_af]
 1314 root         0 SW   [vcap_md]
 1318 root         0 SW   [isp_mon]
 1324 root         0 DW   [mcp100_cb_threa]
 1325 root         0 DW   [mcp100_getjob_t]
 1329 root         0 DW   [favce_cb_thread]
 1330 root         0 DW   [favce_engine0_t]
 1343 root         0 DW   [scaler_add_tabl]
 1346 root         0 DW<  [scaler_callback]
 1347 root         0 DW   [scaler_2ddma_ca]
 1357 root         0 DW   [gm_au_stop0]
 1358 root         0 DW   [gm_au_stop1]
 1359 root         0 SW<  [audio_in]
 1360 root         0 SW<  [audio_out]
 1364 root         0 DW<  [gm_group]
 1365 root         0 DW<  [gm_gs_notify]
 1369 root         0 DW   [gm_enc_cap_out_]
 1370 root         0 DW   [gm_enc_scl_out_]
 1371 root         0 DW   [gm_au_encode_dd]
 1372 root         0 DW   [gm_au_playback_]
 1373 root         0 DW   [gm_vpslv]
 1374 root         0 DW   [gm_vpd_notify]
 1375 root         0 DW<  [datain_callback]
 1376 root         0 DW<  [dataout_callbac]
 1377 root         0 SW<  [dataout_timeout]
 1378 root         0 SW   [usr_decode]
 1425 root      1348 S    telnetd -b 127.0.0.1
 1434 root      2292 S    ./mipc_tool -cmd debug -server 1
 1436 root      1360 R    telnetd -p 9527
 1479 root      2308 S    ./mipc_tool -cmd wd -len 20
 1798 root      1356 S    {dev_watch.sh} /bin/sh ./dev_watch.sh
 1799 root      1360 S    /sbin/getty -L ttyS0 115200 vt100
 1805 root     15636 S    {main} ./mipc cdm -cont-conf ../../../apps/app/ipc/conf/container.conf.cdm
 1814 root      1344 S    sleep 300
 1818 root      6956 S    [system_proxy]
 1825 root         0 SW   [RTW_CMD_THREAD]
 1853 root      1264 S    wpa_supplicant -B -Dwext -c /etc/wpa_supplicant.conf -ira0
 1858 root     73280 S    {main} mipc
 1905 root      1368 S    -sh
 1982 root         0 SW   [kworker/0:3]
 2007 root      1352 R    ps
```
<br>

## General observations

- Hardcoded secrets are shipped in firmware, local device password is also stored in `/tmp/pass.debug` at runtime for root
- Hidden debug tooling is shipped in the web root (remote backdoors)
- Live devices connect to vendor infrastructure
- Remote login/debug RPCs are exposed
- Telnet/debug mechanisms are integrated into the product startup flow
<br>

# Further research
I have tested the hardcoded passwords `pass.mp` and `pass.up` to generate the root password on other Ebitcam devices. For now, it seems like these values are unique on every device. However, the debug features observed on the webserver is not unique and works on all Ebitcam devices.
