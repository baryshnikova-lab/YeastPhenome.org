function getModelID(){
    var out=window.location.pathname.replace(/\/$/,'').split('/');
    return out[out.length-1];
}

django.jQuery(document).ready(function(){
    var $=django.jQuery
    $('.field-ancestry')
     	.find('div')
     	.append('<a href="/admin/phenotypes/observable2/?_to_field=ancestry" class="related-lookup" id="lookup_id_ancestry"></a>');

    var overload=dismissRelatedLookupPopup;
    dismissRelatedLookupPopup=function(win,chosenId){
	if('id_ancestry'===win.name){
	    chosenId+=('000'+getModelID()).substr(-3,3)+'.';
	}
	return overload(win,chosenId);
    }

});
