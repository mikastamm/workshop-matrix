#!/bin/bash
sudo systemctl restart matrix
journalctl -u matrix -f