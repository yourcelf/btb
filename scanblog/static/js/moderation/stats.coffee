unless window.btb?
    window.btb = {}

btb.stats =
    treeMap: (id, data) ->
        tm = new $jit.TM.Squarified
            injectInto: id,
            titleHeight: 15,
            animate: true,
            offset: 0,
            Events:
                enable: true,
                onClick: (node) -> if node then tm.enter(node)
                onRightClick: -> tm.out()
            duration: 1000
            Tips:
                enable: true
                offsetX: 20
                offsetY: 20
                onShow: (tip, node, isLeaf, el) ->
                    $(tip)
                        .html("#{node.name} (#{node.data["$area"]})")
            onCreateLabel: (el, node) ->
                $(el).html("#{node.name} (#{node.data["$area"]})").css({
                    color: "white"
                    border: "none"
                })

        id_counter = 0
        fixData = (node, color) ->
            node.data = '$area': node.size, '$color': "rgb(#{color[0]}, #{color[1]}, #{color[2]})"
            node.id = "id#{id_counter}"
            id_counter += 1
            if node.children?
                for i in [0...node.children.length]
                    color[i % color.length] += 50
                    fixData(node.children[i], color)
            else
                node.children = []
        fixData(data, [0, 0, 0])

        tm.loadJSON(data)
        tm.refresh()

    stackedData: (id, aggregates) ->
        data = {
            label: []
            values: []
        }

        weeks = {}
        for name, agg of aggregates
            data.label.push(name)
            for entry in agg
                unless weeks[entry.week]?
                    weeks[entry.week] = {}
                unless weeks[entry.week][name]?
                    weeks[entry.week][name] = entry.count

        items = for week, entries of weeks
            [week, entries]
        items.sort()

        for [week, entries] in items
            value = {
                label: week.split("T")[0].replace(/-/g, ".")
                values: []
            }
            for name in data.label
                if entries[name]?
                    value.values.push(entries[name])
                else
                    value.values.push(0)
            data.values.push(value)

        ac = new $jit.AreaChart
            injectInto: id
            animate: true
            Margin:
                top: 5
                left: 5
                right: 5
                bottom: 5
            labelOffset: 10
            showAggregates: true
            showLabels: true
            type: 'stacked'
            Label:
                overridable: true
                type: 'HTML'
                size: 10
                family: 'Arial'
                color: 'black'
            Tips:
                enable: true
                onShow: (tip, elem) ->
                    $(tip).html("<b>#{elem.name}</b>: #{elem.value}")
            filterOnClick: true
            restoreOnRightClick: true

        ac.loadJSON(data)

        # Add legend
        legend = ac.getLegend()
        ul = $("<ul class='legend' />")
        for name, color of legend
            ul.append("<li><div class='swatch' style='background-color: #{color}'></div>#{name}</li>")
        $("##{id}").append(ul)

        # Trim labels.
        labelNum = 0
        $("##{id} .node").each ->
            # Show only every 4th label
            unless labelNum % 4 == 0
                $(this).remove()
            else
                $(this).css("width", $(this).width() * 4 + "px")
            labelNum += 1

        ac
    impactChart: (id, flat_data, user_field, l1units, l2units) ->
        colors = [
            [100, 0, 0],
            [0, 100, 0],
            [0, 0, 100],
            [0, 100, 100],
        ]
        make_color = (i, adder) ->
            "rgb(#{colors[i][0] + adder}, #{colors[i][1] + adder}, #{colors[i][2] + adder})"
        
        # Get total count..
        total = 0
        for entry in flat_data
            total += entry.count
        flat_data.sort( (a,b) -> a.count - b.count )


        partitions = []
        for i in [0...4]
            partitions.push
                id: "partition#{i}"
                data: {
                    "$color": make_color(i, 0)
                    "$angularWidth": 0
                    count: 0
                    units: l1units
                }
                children: []

        index = 0
        running_total = 0
        prev = -1
        for entry in flat_data
            running_total += entry.count
            if (running_total > (total / 4) * (index + 1)) and (entry.count != prev)
                index = Math.min(partitions.length - 1, index + 1)
            prev = entry.count
            partition = partitions[index]
            partition.data["$angularWidth"] += entry.count
            partition.data.count += 1
            partition.children.push
                id: "entry#{running_total}"
                name: entry[user_field]
                data: {
                    "$color": make_color(index, parseInt((entry.count / total * 100)))
                    "$angularWidth": entry.count
                    count: entry.count
                    units: l2units
                }
                children: []

        for part in partitions
            part.name = "#{part.children[0].data["$angularWidth"]} to " +
                "#{part.children[part.children.length - 1].data["$angularWidth"]} " +
                "#{l2units}"


        running_total = 0
        data =
            id: "root"
            name: 'Impact'
            data: {'$type': 'none'}
            children: partitions

        sb = new $jit.Sunburst
            injectInto: id
            levelDistance: 110
            Node:
                overridable: true
                type: 'multipie'
            Label:
                type: 'Native'
            NodeStyles:
                enable: true
                type: 'Native'
            Tips:
                enable: true
                onShow: (tip, node) ->
                    tip.innerHTML = "<div class='tip'>#{node.name} (#{node.data.count} #{node.data.units})</div>"
            Events:
                enable: true
                onclick: (node) ->

            onCreateLabel: (el, node) ->
                el.innerHTML = node.name

        sb.loadJSON(data)
        sb.refresh()

