class Robogame {

	server = null;
	port = null;
	secret = null;
	network = null;
	tree = null;

	constructor(secret,server="localhost",port=5000) {
		this.server = server
		this.port = port
		this.secret = secret
	}

	post(url,payload) {
		let xhr = new XMLHttpRequest(); 
		xhr.open("POST", url, false);
		xhr.setRequestHeader("Content-Type", "application/json");
        xhr.send(JSON.stringify(payload));
        return(JSON.parse(xhr.responseText));
	}

	getUrl(path) {
		return("http://"+this.server+":"+this.port+path)
	}

	getNetwork() {
		if (this.network != null) {
			return(this.network);
		}
		var payload = {'secret':this.secret};
		var r = this.post(this.getUrl("/api/v1/resources/network"),payload);
		this.network = r;
		return(this.network);
	}

	getTree() {
		if (this.tree != null) {
			return(this.tree);
		}
		var payload = {'secret':this.secret};
		var r = this.post(this.getUrl("/api/v1/resources/tree"),payload);
		this.tree = r;
		return(this.tree);
	}

	getGameTime() {
		var payload = {'secret':this.secret};
		var r = this.post(this.getUrl("/api/v1/resources/gametime"),payload);
		return(r);
	}

	getRobotInfo() {
		var payload = {'secret':this.secret};
		var r = this.post(this.getUrl("/api/v1/resources/robotinfo"),payload);
		return(r);
	}

	setRobotInterest(interest) {
		var payload = {'secret':this.secret,'Bots':interest};
		var r = this.post(this.getUrl("/api/v1/resources/setinterestbots"),payload);
		return(r);
	}

	setPartInterest(interest) {
		var payload = {'secret':this.secret,'Parts':interest};
		var r = this.post(this.getUrl("/api/v1/resources/setinterestparts"),payload);
		return(r);
	}

	setBets(bets) {
		var payload = {'secret':this.secret,'Bets':bets}
		var r = this.post(this.getUrl("/api/v1/resources/setbets"),payload)
		return(r);
	}

	getHints() {
		var payload = {'secret':this.secret}
		var r = this.post(this.getUrl("/api/v1/resources/gethints"),payload)
		return(r);
	}

	setReady() {
		var payload = {'secret':this.secret};
		var r = this.post(this.getUrl("/api/v1/resources/setready"),payload);
		return(r);
	}

}
