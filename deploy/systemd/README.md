## use systemd to run the application

```
mkdir -p ~/.config/systemd/user
cp *.service ~/.config/systemd/user/.

# make sure the run the migration, seed database etc

systemctl --user start gitcrawler
systemctl --user start celery
systemctl --user start flower

# if the processes get killed after logout, run this as root
loginctl --enable-linger <login_name>
```
