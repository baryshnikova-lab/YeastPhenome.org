function classes(root) {
    var classes = [];
    var domain = [];

    function recurse(name, node) {
	if(('size' in node) && (0 != node.size)){
	    classes.push({
		packageName:name,
		className:node.name,
		value:node.size,
		id:node.id,
	    });
	    if(-1 == domain.indexOf(node.size)){
		domain.push(node.size);
	    }
	}

	if (node.children) node.children.forEach(
	    function(child){
		recurse(node.name, child);
	    }
	);
    }
    recurse(null, root);
    return {children:classes,domain:domain.sort(function(a,b){
	return a-b;
    })};
}



$(document).ready(function(){
    // Basically nicked from http://bl.ocks.org/mbostock/4063530

    var diameter=960;
    var format=d3.format(",d");

    var flat=classes(flare);
    console.log(flat);
    //var color=d3.scale.category20c().domain(flat.domain);
    var color=d3.scale.ordinal()
	.domain(flat.domain)
	.range(colorbrewer.BuGn[9]);

    var bubble=d3.layout.pack()
	.sort(function(a,b){
	    return b.className.localeCompare(a.className)
	})
	.size([diameter,diameter])
	.padding(1.5)
    ;
    var svg=d3.select("#graphic").append("svg")
	.attr("width",diameter)
	.attr("height",diameter)
	.attr("class","bubble")
    ;

    var node = svg.selectAll(".node")
	.data(bubble.nodes(flat)
	      .filter(function(d) { return !d.children; }))
	.enter().append("g")
	.attr("class", "node")
	.attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; })
	.append('a')
	.attr('xlink:href',function(d){
	    if('id' in d){
		return '/'+flare.name+'/'+d.id+'/';
	    }
	    return null;
	})
    ;

    node
	.append("title")
	.text(function(d) { return d.className + ": " + format(d.value); })
    ;

    node.append("circle")
	.attr("r", function(d) { 
	    return d.r;
	})
	.style("fill", function(d) {
	    if(0==d.value){
		console.log(d.value);
	    }
	    return color(d.value);
	})
    ;

    node.append("text")
	.attr("dy", ".3em")
	.style("text-anchor", "middle")
	.text(function(d) { return d.className.substring(0, (d.r/3)-2); });

    //d3.select(self.frameElement).style("height", diameter + "px");

    var key=$('#legend');
    key.append('<tr><th>Papers</th><th>Color</th></tr>');
    color.domain().sort(function(a,b){
	return a-b;
    }).forEach(function(d){
	key.append('<tr><td>'+d+'</td><td style="background:'+
		   color(d)+'"></td></tr>');
    });
});
