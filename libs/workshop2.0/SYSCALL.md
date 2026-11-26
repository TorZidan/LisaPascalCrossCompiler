# `SYSCALL` (`SYSCALL.obj`) — Lisa OS 2.0 System Call Interface

[Back to Library Index](LIBRARIES.md)

Direct Pascal interface to the Apple Lisa OS 2.0 kernel: catalog/file I/O, data segments, processes, events, timers, pipes, and device control.

- **Object file**: `libs/workshop2.0/SYSCALL.obj` (Plain unit (`.obj`))
- **Contents**: 1 unit, 77 procedures/functions

## Importing and Linking

```pascal
USES {$U SysCall.obj} SysCall;
```

```sh
LISA_BOOT=libs/workshop2.0 pascal/lpc.py --2.0 --link=IOSPASLIB,SYSCALL MYPROG
```

## Units in This Library

| Unit | 8-Char Symbol | `USES` Dependencies | Routines | Summary |
|---|---|---|---|---|
| [`SysCall`](#unit-syscall) | `SYSCALL` | — | 77 | Defines the public Lisa Operating System kernel interface, exposing system calls and data structures for hierarchical catalog and file I/O, preemptive/non-preemptive process management, LDSN virtual memory data segments, named exceptions, interprocess event channels, real-time clock timers, and hardware/PMEM configuration. |

---

## Unit SysCall

Defines the public Lisa Operating System kernel interface, exposing system calls and data structures for hierarchical catalog and file I/O, preemptive/non-preemptive process management, LDSN virtual memory data segments, named exceptions, interprocess event channels, real-time clock timers, and hardware/PMEM configuration.

- **Import**: `USES {$U SysCall.obj} SysCall;`
- **Unit kind**: `INTRINSIC` (`SYSCALL`)

### Procedures and Functions

| Routine | Signature | Description |
|---|---|---|
| `MAKE_FILE` | `procedure MAKE_FILE(var ecode: integer; var path: pathname; label_size: integer);` | Creates a new Lisa OS disk file and catalog entry at `path` with an optional user file label of `label_size` bytes. |
| `MAKE_PIPE` | `procedure MAKE_PIPE(var ecode: integer; var path: pathname; label_size: integer);` | Creates a new interprocess FIFO pipe object at catalog `path` with an optional file label of `label_size` bytes. |
| `MAKE_CATALOG` | `procedure MAKE_CATALOG(var ecode: integer; var path: pathname; label_size: integer);` | Creates a new Lisa OS subdirectory catalog at `path` with an optional catalog label of `label_size` bytes. |
| `MAKE_LINK` | `procedure MAKE_LINK(var ecode: integer; var path, ref: pathname; label_size: integer);` | Creates a catalog link entry at `path` pointing to target pathname `ref`, with an optional label of `label_size` bytes. |
| `KILL_OBJECT` | `procedure KILL_OBJECT(var ecode: integer; var path: pathname);` | Removes the catalog entry and deletes the file, pipe, link, or empty catalog at `path` (deferring disk reclamation until closed if open). |
| `UNKILL_FILE` | `procedure UNKILL_FILE(var ecode: integer; refnum: integer; var new_name: e_name);` | Restores an open, previously killed file (`refnum`) into its directory catalog under `new_name`. |
| `OPEN` | `procedure OPEN(var ecode: integer; var path: pathname; var refnum: integer; manip: mset);` | Opens the file, pipe, or device at `path` with access flags `manip` (`dread`, `dwrite`, `append`, `private`, `global_refnum`), returning its descriptor in `refnum`. |
| `CLOSE_OBJECT` | `procedure CLOSE_OBJECT(var ecode: integer; refnum: integer);` | Flushes buffered changes and closes the open file, pipe, or device reference `refnum`. |
| `READ_DATA` | `procedure READ_DATA(var ecode: integer; refnum: integer; data_addr: longint; count: longint; var actual: longint; mode: iomode; offset: longint);` | Reads up to `count` bytes from open object `refnum` into memory address `data_addr` using `mode` (`absolute`, `relative`, or `sequential`) and `offset`, returning bytes read in `actual`. |
| `WRITE_DATA` | `procedure WRITE_DATA(var ecode: integer; refnum: integer; data_addr: longint; count: longint; var actual: longint; mode: iomode; offset: longint);` | Writes `count` bytes from memory address `data_addr` to open object `refnum` using `mode` (`absolute`, `relative`, or `sequential`) and `offset`, returning bytes written in `actual`. |
| `FLUSH` | `procedure FLUSH(var ecode: integer; refnum: integer);` | Flushes all modified system buffers and file metadata for open file `refnum` out to disk. |
| `LOOKUP` | `procedure LOOKUP(var ecode: integer; var path: pathname; var attributes: fs_info);` | Retrieves full volume, device, or file attributes (`fs_info`) for catalog `path` without opening the object. |
| `INFO` | `procedure INFO(var ecode: integer; refnum: integer; var refinfo: fs_info);` | Retrieves full volume, device, or file attributes (`fs_info`), including current file mark and EOF status, for open object `refnum`. |
| `ALLOCATE` | `procedure ALLOCATE(var ecode: integer; refnum: integer; contiguous: boolean; count: longint; var actual: longint);` | Preallocates `count` bytes of disk storage (optionally `contiguous`) to open file `refnum`, returning the actual byte count allocated in `actual`. |
| `TRUNCATE` | `procedure TRUNCATE(var ecode: integer; refnum: integer);` | Sets the logical end-of-file of open file `refnum` to its current file position (`fmark`), discarding any logical data past that point. |
| `COMPACT` | `procedure COMPACT(var ecode: integer; refnum: integer);` | Releases unused physical disk blocks allocated beyond the logical end-of-file of open file `refnum` back to volume free space. |
| `RENAME_ENTRY` | `procedure RENAME_ENTRY(var ecode: integer; var path: pathname; var newname: e_name);` | Renames the existing catalog entry at `path` to `newname` within the same parent catalog. |
| `READ_LABEL` | `procedure READ_LABEL(var ecode: integer; var path: pathname; data_addr: longint; count: longint; var actual: longint);` | Reads up to `count` bytes from the user metadata label of `path` into memory at `data_addr`, returning bytes transferred in `actual`. |
| `WRITE_LABEL` | `procedure WRITE_LABEL(var ecode: integer; var path: pathname; data_addr: longint; count: longint; var actual: longint);` | Writes `count` bytes from memory at `data_addr` into the user metadata label of `path`, returning bytes transferred in `actual`. |
| `MOUNT` | `procedure MOUNT(var ecode: integer; var vname: e_name; var password: e_name; var devname: e_name);` | Mounts the Lisa OS file system volume on block device `devname` (validating `password` if protected) and returns its volume name in `vname`. |
| `UNMOUNT` | `procedure UNMOUNT(var ecode: integer; var vname: e_name);` | Flushes buffers and unmounts the mounted file system volume `vname`. |
| `SET_WORKING_DIR` | `procedure SET_WORKING_DIR(var ecode: integer; var path: pathname);` | Sets the calling process's current working directory/catalog prefix to `path`. |
| `GET_WORKING_DIR` | `procedure GET_WORKING_DIR(var ecode: integer; var path: pathname);` | Returns the calling process's current working directory/catalog prefix in `path`. |
| `SET_SAFETY` | `procedure SET_SAFETY(var ecode: integer; var path: pathname; on_off: boolean);` | Enables (`on_off = TRUE`) or disables (`on_off = FALSE`) the safety-switch protection attribute on file `path`. |
| `DEVICE_CONTROL` | `procedure DEVICE_CONTROL(var ecode: integer; var path: pathname; var cparm: dctype);` | Executes a device-driver control or status operation specified by `cparm` (`dctype`, such as RS-232 configuration, console event polling, or disk sparing) on device `path`. |
| `RESET_CATALOG` | `procedure RESET_CATALOG(var ecode: integer; var path: pathname);` | Initializes the calling process's directory scan cursor to the start of catalog `path` for subsequent `GET_NEXT_ENTRY` or `LOOKUP_NEXT_ENTRY` calls. |
| `GET_NEXT_ENTRY` | `procedure GET_NEXT_ENTRY(var ecode: integer; var prefix, entry: e_name);` | Returns in `entry` the next catalog entry name matching leading filter `prefix` from the catalog or subtree scan started by `RESET_CATALOG` or `RESET_SUBTREE`. |
| `SET_FILE_INFO` | `procedure SET_FILE_INFO(var ecode: integer; refnum: integer; fsi: fs_info);` | Updates user-modifiable file metadata fields (such as `user_type`, `user_subtype`, and timestamps from `fsi`) on open file `refnum`. |
| `My_ID` | `function My_ID: longint;` | Returns the unique global Lisa OS process identifier (`longint`) of the calling process. |
| `Info_Process` | `procedure Info_Process(var errnum: integer; proc_id: longint; var proc_info: procinfoRec);` | Retrieves process state, priority, parent ID, program pathname, and memory-residency status (`procinfoRec`) for process `proc_id`. |
| `Yield_CPU` | `procedure Yield_CPU(var errnum: integer; to_any: boolean);` | Relinquishes the calling process's remaining CPU quantum to ready processes of at least equal priority, or to any ready process when `to_any` is `TRUE`. |
| `SetPriority_Process` | `procedure SetPriority_Process(var errnum: integer; proc_id: longint; new_priority: integer);` | Sets the scheduler dispatch priority (`1..255`) of process `proc_id` to `new_priority`. |
| `Suspend_Process` | `procedure Suspend_Process(var errnum: integer; proc_id: longint; susp_family: boolean);` | Suspends execution of process `proc_id` (and its descendant processes if `susp_family` is `TRUE`) until reactivated by `Activate_Process`. |
| `Activate_Process` | `procedure Activate_Process(var errnum: integer; proc_id: longint; act_family: boolean);` | Resumes execution of suspended process `proc_id` (and its descendant processes if `act_family` is `TRUE`). |
| `Kill_Process` | `procedure Kill_Process(var errnum: integer; proc_id: longint);` | Forces immediate asynchronous termination of process `proc_id` and any descendant child processes. |
| `Terminate_Process` | `procedure Terminate_Process(var errnum: integer; event_ptr: p_s_eventblk);` | Terminates the calling process normally and optionally delivers termination message `event_ptr^` to its parent's event channel. |
| `Make_Process` | `procedure Make_Process(var errnum: integer; var proc_id: longint; var progfile: pathname; var entryname: namestring; evnt_chn_refnum: integer);` | Creates and starts a new process running executable `progfile` (at entry point `entryname`) with termination events routed to `evnt_chn_refnum`, returning its process ID in `proc_id`. |
| `Sched_Class` | `procedure Sched_Class(var errnum: integer; non_preempt: boolean);` | Places the calling process into (`non_preempt = TRUE`) or out of (`non_preempt = FALSE`) nested non-preemptive scheduling mode. |
| `make_dataseg` | `procedure make_dataseg(var errnum: integer; var segname: pathname; mem_size, disc_size: longint; var refnum: integer; var segptr: longint; ldsn: integer; dstype: Tdstype);` | Creates and maps a shared or private (`dstype`) data segment `segname` of `mem_size` RAM bytes and `disc_size` swap bytes at logical segment `ldsn`, returning `refnum` and base address `segptr`. |
| `kill_dataseg` | `procedure kill_dataseg(var errnum: integer; var segname: pathname);` | Deletes named data segment `segname` and frees its backing disk storage once all processes close it. |
| `open_dataseg` | `procedure open_dataseg(var errnum: integer; var segname: pathname; var refnum: integer; var segptr: longint; ldsn: integer);` | Opens existing named data segment `segname` and maps it into the calling process's address space at logical segment `ldsn`, returning `refnum` and base address `segptr`. |
| `close_dataseg` | `procedure close_dataseg(var errnum: integer; refnum: integer);` | Unmaps and closes open data segment `refnum` in the calling process's address space. |
| `size_dataseg` | `procedure size_dataseg(var errnum: integer; refnum: integer; deltamemsize: longint; var newmemsize: longint; deltadiscsize: longint; var newdiscsize: longint);` | Resizes open data segment `refnum` by `deltamemsize` bytes in memory and `deltadiscsize` bytes on disk, returning the resulting sizes in `newmemsize` and `newdiscsize`. |
| `info_dataseg` | `procedure info_dataseg(var errnum: integer; refnum: integer; var dsinfo: dsinfoRec);` | Retrieves memory/disk sizes, LDSN slot, base pointer, open count, binding/presence flags, access mode, and volume name (`dsinfoRec`) for open data segment `refnum`. |
| `setaccess_dataseg` | `procedure setaccess_dataseg(var errnum: integer; refnum: integer; readonly: boolean);` | Configures MMU protection for open data segment `refnum` in the calling process as read-only (`readonly = TRUE`) or read/write (`readonly = FALSE`). |
| `unbind_dataseg` | `procedure unbind_dataseg(var errnum: integer; refnum: integer);` | Unpins open data segment `refnum` in physical RAM so the virtual memory manager can swap it out to disk when memory is needed. |
| `bind_dataseg` | `procedure bind_dataseg(var errnum: integer; refnum: integer);` | Pins open data segment `refnum` in physical RAM so it remains resident and cannot be swapped out to disk. |
| `info_ldsn` | `procedure info_ldsn(var errnum: integer; ldsn: integer; var refnum: integer);` | Returns in `refnum` the data segment reference number currently mapped at logical data segment number `ldsn` in the calling process. |
| `flush_dataseg` | `procedure flush_dataseg(var errnum: integer; refnum: integer);` | Writes the in-memory contents of open data segment `refnum` out to its backing disk storage. |
| `mem_info` | `procedure mem_info(var errnum: integer; var swapspace, dataspace, cur_codesize, max_codesize: longint);` | Returns available system `swapspace`, available physical `dataspace`, current resident code size `cur_codesize`, and maximum code space `max_codesize` in bytes. |
| `info_address` | `procedure info_address(var errnum: integer; address: longint; var refnum: integer);` | Identifies the open data segment containing virtual `address` in the calling process and returns its descriptor in `refnum`. |
| `declare_excep_hdl` | `procedure declare_excep_hdl(var errnum: integer; var excep_name: t_ex_name; entry_point: longadr);` | Binds exception handler routine `entry_point` to named exception `excep_name` for the calling process. |
| `disable_excep` | `procedure disable_excep(var errnum: integer; var excep_name: t_ex_name; queue: boolean);` | Disables immediate delivery of named exception `excep_name` in the calling process, queuing raised occurrences if `queue` is `TRUE` or ignoring them if `FALSE`. |
| `enable_excep` | `procedure enable_excep(var errnum: integer; var excep_name: t_ex_name);` | Re-enables delivery of named exception `excep_name` in the calling process and dispatches any queued occurrences. |
| `signal_excep` | `procedure signal_excep(var errnum: integer; var excep_name: t_ex_name; excep_data: t_ex_data);` | Signals named exception `excep_name` in the calling process with 48-byte exception data block `excep_data`. |
| `info_excep` | `procedure info_excep(var errnum: integer; var excep_name: t_ex_name; var excep_status: t_ex_sts);` | Returns the current state (`enabled`, `queued`, `ignored`), occurrence flag, queued count, and handler address (`t_ex_sts`) for exception `excep_name`. |
| `flush_excep` | `procedure flush_excep(var errnum: integer; var excep_name: t_ex_name);` | Clears and discards all queued pending occurrences of named exception `excep_name` for the calling process. |
| `make_event_chn` | `procedure make_event_chn(var errnum: integer; var event_chn_name: pathname);` | Creates a named interprocess event channel at catalog path `event_chn_name`. |
| `kill_event_chn` | `procedure kill_event_chn(var errnum: integer; var event_chn_name: pathname);` | Removes the named interprocess event channel at catalog path `event_chn_name`. |
| `open_event_chn` | `procedure open_event_chn(var errnum: integer; var event_chn_name: pathname; var refnum: integer; var excep_name: t_ex_name; receiver: boolean);` | Opens event channel `event_chn_name` as a receiver (`receiver = TRUE`, optionally signaling `excep_name` for call channels) or sender (`receiver = FALSE`), returning `refnum`. |
| `close_event_chn` | `procedure close_event_chn(var errnum: integer; refnum: integer);` | Closes the calling process's open reference `refnum` to an event channel. |
| `info_event_chn` | `procedure info_event_chn(var errnum: integer; refnum: integer; var chn_info: t_chn_sts);` | Retrieves channel kind (`wait_ec` or `call_ec`), queued event count, open receiver/sender counts, and pathname (`t_chn_sts`) for open event channel `refnum`. |
| `wait_event_chn` | `procedure wait_event_chn(var errnum: integer; var wait_list: t_waitlist; var refnum: integer; event_ptr: p_r_eventblk);` | Suspends the calling process until an event arrives on any channel listed in `wait_list`, returning the active channel's `refnum` and copying the received event into `event_ptr^`. |
| `flush_event_chn` | `procedure flush_event_chn(var errnum: integer; refnum: integer);` | Discards all unread events currently queued on open event channel `refnum`. |
| `send_event_chn` | `procedure send_event_chn(var errnum: integer; refnum: integer; event_ptr: p_s_eventblk; interval: timestmp_interval; clktime: time_rec);` | Posts event message `event_ptr^` to open event channel `refnum`, either immediately or scheduled after relative `interval` / at clock time `clktime`. |
| `delay_time` | `procedure delay_time(var errnum: integer; interval: timestmp_interval; clktime: time_rec);` | Suspends the calling process until relative duration `interval` elapses or absolute clock time `clktime` is reached. |
| `get_time` | `procedure get_time(var errnum: integer; var gmt_time: time_rec);` | Reads the hardware real-time clock and returns the current Greenwich Mean Time in `gmt_time` (`time_rec`). |
| `set_local_time_diff` | `procedure set_local_time_diff(var errnum: integer; hour: hour_range; minute: minute_range);` | Sets the system-wide GMT-to-local time zone offset (`hour` and `minute`) used by `convert_time`, returning any OS error code in `errnum`. |
| `convert_time` | `procedure convert_time(var errnum: integer; var gmt_time: time_rec; var local_time: time_rec; to_gmt: boolean);` | Converts timestamps between Greenwich Mean Time (`gmt_time`) and local time (`local_time`), translating local-to-GMT when `to_gmt` is `TRUE` and GMT-to-local otherwise. |
| `MACH_INFO` | `procedure MACH_INFO(var ecode: integer; var the_info: minfo);` | Returns machine hardware identification in `the_info` (`minfo`), reporting the CPU board revision, I/O board model, and total physical memory size. |
| `ENABLEDBG` | `function ENABLEDBG(enableit: boolean): boolean;` | Enables (`enableit = TRUE`) or disables (`enableit = FALSE`) the resident LisaBug debugger if loaded, locking or unlocking its code/data segments and returning the resulting state. |
| `OSBOOTVOL` | `function OSBOOTVOL(var error: integer): tports;` | Returns the volume name of the Lisa OS startup/boot disk in `Volname`. |
| `GET_CONFIG_NAME` | `procedure GET_CONFIG_NAME(var error: integer; devpostn: tports; var devname: e_name);` | Retrieves the configured Lisa OS device name (`devname`, without a leading `'-'`) bound to hardware port or slot `devpostn`, returning any error code in `error`. |
| `DISK_LIKELY` | `function DISK_LIKELY(var error: integer; devpostn: tports): boolean;` | Returns `TRUE` if hardware port or slot position `devpostn` has a mountable block-storage disk device configured, returning any OS status code in `error`. |
| `CARDS_EQUIPPED` | `procedure CARDS_EQUIPPED(var error: integer; var in_slot: slot_array);` | Returns the expansion card identification codes installed in hardware expansion slots 1 through 3 in `in_slot`. |
| `Read_PMem` | `procedure Read_PMem(var errnum: integer; var my_pMem: pMemRec);` | Reads the 64-byte system parameter memory block into `my_pMem` and reports any boot-time parameter memory or disk-snapshot warning code in `errnum`. |
| `Write_PMem` | `procedure Write_PMem(var errnum: integer; my_pMem: pMemRec);` | Writes 64-byte parameter memory image `my_pMem` with an updated timestamp and checksum to system globals, hardware parameter memory, and the boot-disk snapshot. |
