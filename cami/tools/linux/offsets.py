import gdb
import sys
import json
from collections import OrderedDict
import re


functions = [
    "commit_creds",
    "arch_jump_label_transform",
    "module_param_sysfs_setup",
    "module_param_sysfs_remove",
    "wake_up_new_task",
    "flush_old_exec",
    "do_exit",
    "arch_ptrace",
    "compat_arch_ptrace",
    "process_vm_rw_core",
    "__vma_link_rb",
    "change_protection",
    "vma_adjust",
    "__vma_adjust",
    "vma_rb_erase",
    "__vma_rb_erase",
    "expand_downwards",
    "complete_signal",
    "text_poke",
    "__text_poke",
    "ftrace_write",
    "panic",
    "crash_kexec",
    "__access_remote_vm",
    "mprotect_fixup",
    "do_munmap",
    "vma_adjust",
]

class Offsets(gdb.Command):
    def __init__(self):
        super (Offsets, self).__init__ ('all-offsets', gdb.COMMAND_DATA)

    def dump_struct(self, struct, fields=[], parent_offset=0):
        for field in struct.fields():
            offset  = parent_offset + field.bitpos // 8
            if not field.name:
                self.dump_struct(field.type, fields, offset)
            else:
                fields[field.name] = offset


    def get_fields(self, name):
        mbrs = OrderedDict()
        st = None
        st = gdb.lookup_type(name)
        self.dump_struct(st, fields=mbrs)
        mbrs["sizeof"] = st.sizeof
        return mbrs


    def invoke(self, arg, from_tty):
        argv = gdb.string_to_argv(arg)
        if len(argv) != 1:
            raise gdb.GdbError("Please specify the output file.")

        structs = OrderedDict()

        names = gdb.execute("info types", to_string=True)

        rx = re.compile("struct [a-zA-Z_][A-Za-z0-9_]*")
        structs = rx.findall(names)
        print(len(structs))

        output = {}
        for struct in structs:
            try:
                output[struct] = self.get_fields(struct)
            except Exception as e:
                print("Exception for [%s]. Will skip: " % struct, file=sys.stderr)
                print(e, file=sys.stderr)
                print("Will skip...", file=sys.stderr)

        ver = gdb.execute("p linux_banner", to_string=True)

        rx = re.compile("[0-9]+\.[0-9]+\.[0-9]+[^ ]*")
        ver = rx.findall(ver)
        output["_KERNEL_VERSION_"] = ver[0] + "*"

        output["_FUNCTIONS_"] = []

        for func in functions:
            try:
                out = gdb.execute("whatis " + func)
                output["_FUNCTIONS_"].append(func)
            except:
                pass


        with open(argv[0], "w") as outfile:
            json.dump(output, outfile, indent=4)

        return

Offsets()
