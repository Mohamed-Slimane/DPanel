(function(){
	function check_wp()
	{
		if (document.documentElement.outerHTML.match(/<(img|link|script) [^>]+wp-content/i)){
			return 'is_wp';
		} else {
			return 'is_nowp';
		}
	}

	this.extension_check_wp = check_wp;
}());


