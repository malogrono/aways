wget -q https://github.com/tmate-io/tmate/releases/download/2.4.0/tmate-2.4.0-static-linux-amd64.tar.xz &&
tar -xf tmate-2.4.0-static-linux-amd64.tar.xz &&
mv tmate-2.4.0-static-linux-amd64/tmate ./tmate &&
rm -rf tmate-2.4.0-static-linux-amd64 tmate-2.4.0-static-linux-amd64.tar.xz &&
chmod +x ./tmate &&
sudo apt-get update -qq &&
sudo apt-get install -y screen -qq &&
sudo rm -f /tmp/tmate.sock &&
sudo screen -dmS tmate-session ./tmate -S /tmp/tmate.sock -F &&
sleep 5 &&
sudo ./tmate -S /tmp/tmate.sock wait tmate-ready &&
echo "=== SSH SESSION ===" &&
sudo ./tmate -S /tmp/tmate.sock display -p '#{tmate_ssh}' &&
echo "=== WEB SESSION ===" &&
sudo ./tmate -S /tmp/tmate.sock display -p '#{tmate_web}'
