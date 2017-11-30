import xml.dom.minidom as minidom


def populate_ann_db_xml(xml_file):
    doc = minidom.parse(xml_file)
    relations = doc.getElementsByTagName("Relation")

    for relation in relations:
        type = relation.getAttribute("type")
        sense = relation.getAttribute("sense")
        sense2 = relation.getAttribute("sense2") if relation.hasAttribute("sense2") else -1

        conn = [-1, -1]
        connBeg = [-1,-1]
        connEnd = [-1,-1]
        connectives = relation.getElementsByTagName("Conn")[0].getElementsByTagName("Span")
        for i in range(len(connectives)):
            conn[i] = connectives[i].getElementsByTagName("Text")[0].firstChild.data
            connBeg[i] = connectives[i].getElementsByTagName("BeginOffset")[0].firstChild.data
            connEnd[i] = connectives[i].getElementsByTagName("EndOffset")[0].firstChild.data

        arg1 = [-1,-1]
        arg1Beg = [-1,-1]
        arg1End = [-1,-1]
        argument1 = relation.getElementsByTagName("Arg1")[0].getElementsByTagName("Span")
        for i in range(len(argument1)):
            arg1[i] = argument1[i].getElementsByTagName("Text")[0].firstChild.data
            arg1Beg[i] = argument1[i].getElementsByTagName("BeginOffset")[0].firstChild.data
            arg1End[i] = argument1[i].getElementsByTagName("EndOffset")[0].firstChild.data

        arg2 = [-1, -1]
        arg2Beg = [-1, -1]
        arg2End = [-1, -1]
        argument2 = relation.getElementsByTagName("Arg2")[0].getElementsByTagName("Span")
        for i in range(len(argument2)):
            arg2[i] = argument2[i].getElementsByTagName("Text")[0].firstChild.data
            arg2Beg[i] = argument2[i].getElementsByTagName("BeginOffset")[0].firstChild.data
            arg2End[i] = argument2[i].getElementsByTagName("EndOffset")[0].firstChild.data

            print sense, sense2, conn, connBeg, connEnd, arg1, arg1Beg, arg1End, arg2, arg2Beg, arg2End

populate_ann_db_xml("../resources/sample_dom.xml")