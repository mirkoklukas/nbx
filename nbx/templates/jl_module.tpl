# # # # # # # # # # # # # # # # # # # 
#                                   # 
#   This is an auto-generated file  # 
#   based on the jupyter notebook   # 
#
#   >   ``{{nbname}}''
#
#                                   #
# # # # # # # # # # # # # # # # # # #
{% if jl_module is defined %}
##################################### 
module {{jl_module}}  
#####################################
{% endif %}{% for line in lines %}{{line}}{% if not loop.last %}
{% endif %}{% endfor %}
{% if jl_module is defined %}
#####################################
end  
#####################################
{% endif %}