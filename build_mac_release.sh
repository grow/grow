#!/bin/bash
rm -rf build
VERSION=`cat grow/VERSION`
pyinstaller grow.spec
#sips -i macgrow/icon.icns
#DeRez -only icns macgrow/icon.icns > build/tmpicon.rsrc
#Rez -append build/tmpicon.rsrc -o dist/grow
#SetFile -a C dist/grow
#rm build/tmpicon.rsrc
chmod +x dist/grow
cd dist
zip -r Grow-SDK-Mac-${VERSION}.zip grow
cd ..
echo "Built: dist/Grow-SDK-Mac-${VERSION}.zip"
