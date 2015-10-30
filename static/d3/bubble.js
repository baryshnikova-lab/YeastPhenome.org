function classes(root) {
    var classes = [];

    function recurse(name, node) {
	if('size' in node){
	    classes.push({
		packageName:name,
		className:node.name,
		value:node.size,
		id:node.id,
	    })
	}

	if (node.children) node.children.forEach(
	    function(child){
		recurse(node.name, child);
	    }
	);
    }
    recurse(null, root);
    return {children: classes};
}



$(document).ready(function(){
    // Basically nicked from http://bl.ocks.org/mbostock/4063530

    var diameter=960;
    var format=d3.format(",d");
    var color=d3.scale.category20c();


    var bubble=d3.layout.pack()
	.sort(null)
	.size([diameter,diameter])
	.padding(1.5)
    ;
    var svg=d3.select("#graphic").append("svg")
	.attr("width",diameter)
	.attr("height",diameter)
	.attr("class","bubble")
    ;

    var node = svg.selectAll(".node")
	.data(bubble.nodes(classes(flare))
	      .filter(function(d) { return !d.children; }))
	.enter().append("g")
	.attr("class", "node")
	.attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; })
	.append('a')
	.attr('xlink:href',function(d){
	    console.log(d);
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
	.attr("r", function(d) { return d.r; })
	.style("fill", function(d) { return color(d.packageName); });

    node.append("text")
	.attr("dy", ".3em")
	.style("text-anchor", "middle")
	.text(function(d) { return d.className.substring(0, (d.r/3)-2); });

    //d3.select(self.frameElement).style("height", diameter + "px");

});
