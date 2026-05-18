#!/usr/bin/env bash

echo "Downloading data"
wget "https://aleph.nkp.cz/data/aut_ph.xml.gz" -O aut_ph.xml.gz
gunzip aut_ph.xml.gz

echo "Done"
