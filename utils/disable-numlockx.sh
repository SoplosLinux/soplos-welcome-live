#!/bin/sh
sed -i 's/^greeter-setup-script=\/usr\/bin\/numlockx on/#greeter-setup-script=\/usr\/bin\/numlockx on/' /etc/lightdm/lightdm.conf
