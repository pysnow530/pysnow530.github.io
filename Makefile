server:
	hexo server

pub:
	rm -rf public
	hexo generate
	rm -rf ../pysnow530.github.io-master/*
	mv public/* ../pysnow530.github.io-master/
	(cd ../pysnow530.github.io-master/ && git add . && git commit -m up)
