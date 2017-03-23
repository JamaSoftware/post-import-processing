from core import PostProcess
from core import Id_Handler

pp = PostProcess()                          ## initializes post=processor class
# pp.process(["R_OSSI-SET-3"])                ## handles post-processing requirements EXCEPT for hyperlink creations
# pp.establish_all_links(["R_OSSI-SET-3"])    ## establishes all hyperlinks within items referencing other items in the project


id_handler = Id_Handler()
id_handler.execute(["CPA-SET-1"])

print "done"





# pp.process(["CPA-SET-2"])
# pp.establish_links(["CPA-SET-2"])
# pp.establish_links("CPA-SET-1")
# pp.process(["CLDEV-SET-15"])
# pp.establish_links("CLDEV-SET-15")

