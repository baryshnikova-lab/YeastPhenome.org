function position() {
    this.style("left", function(d) { return d.x + "px"; })
	.style("top", function(d) { return d.y + "px"; })
	.style("width", function(d) { return Math.max(0, d.dx - 1) + "px"; })
	.style("height", function(d) { return Math.max(0, d.dy - 1) + "px"; });
}

$(document).ready(function(){
    // from http://bl.ocks.org/mbostock/4063582

    var margin = {top: 40, right: 10, bottom: 10, left: 10};
    var width = 960 - margin.left - margin.right;
    var height = 500 - margin.top - margin.bottom;

    var color = d3.scale.category20c();

    var treemap = d3.layout.treemap()
	.size([width, height])
	.sticky(true)
	.value(function(d) { return d.size; });

    $('#graphic').before('<form><label><input type="radio" name="mode" value="size" checked> Size</label><label><input type="radio" name="mode" value="count"> Count</label></form>');

    var div=d3.select("#graphic")
	.style("position", "relative")
	.style("width", (width + margin.left + margin.right) + "px")
	.style("height", (height + margin.top + margin.bottom) + "px")
	.style("left", margin.left + "px")
	.style("top", margin.top + "px");

    // //

    var node = div.datum(flare).selectAll(".node")
	.data(treemap.nodes)
	.enter().append("div")
	.call(position)
	.style("background", function(d) { return d.children ? color(d.name) : null; })
	.attr("class", "node")
    ;

    node.append('a')
	.attr('href',function(d){
	    if('href' in d){
		return d.href
	    }
	    return null;
	})
	.style('color','black')
	.text(function(d) { return d.children ? null : d.name; })
    ;


    d3.selectAll("input").on("change", function change() {
	var value = this.value === "count"
            ? function() { return 1; }
        : function(d) { return d.size; };
	
	node
            .data(treemap.value(value).nodes)
	    .transition()
            .duration(1500)
            .call(position);
    });
});
