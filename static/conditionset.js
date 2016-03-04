function addConditionSetAs(){
    var $=django.jQuery;
    var query_string=[
	'name=' + $('#id_name').val(),
	'conditions=' + $('#id_conditions_to').find('option').map(function(){ return $(this).attr('value') }).get().join(',')
    ];
    window.location=encodeURI('/admin/conditions/conditionset/add?' + query_string.join('&'));
}

django.jQuery(document).ready(function(){
    var $=django.jQuery;
    var sr=$('.submit-row');
    if(sr.length>0){
	$('.object-tools').
	    append('<li><a class="addlink" onclick="addConditionSetAs()" href="#">Add condition set as...</a></li>');
    }
});
