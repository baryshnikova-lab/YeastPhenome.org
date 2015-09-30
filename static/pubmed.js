var yp={
    pubmed:{
	go:function(){
	    console.log('yo!');	
	}
    }
};

$(document).ready(function(){
    var paper=$('[itemscope=paper');
    var pmid=paper.find('[itemprop=PMID]').text();
    var url='/static/MEDLINE/'+pmid+'.txt';

    $.get(url,function(data){
	var lines=data.split("\n");
	var prop=false;
	var medline={};
	for(var i in lines){
	    var line=lines[i];
	    // MEDLINE always has the split at the same place...
	    if('-'===line.charAt(4)){
		// ...so there might be extra padding to remove.
		prop=line.slice(0,4).trim();
		var val=line.slice(6);
		if(medline[prop]){
		    medline[prop].push(val);
		}else{
		    medline[prop]=[val];
		}
	    }else if(prop){
		medline[prop][medline[prop].length-1]+=' '+line.trim();
	    }
	}
	['TI','FAU','CRDT','AB'].forEach(function(prop){
	    paper.find('[itemprop='+prop+']')
		.text(medline[prop].join(' • '));
	})
    }).fail(function(){
	paper.find('.remove_on_error').remove()
    })
	

});
