---
layout: post
title:  "Google CTF 2022 - Segfault Labyrinth"
categories: writeup
tags: google-ctf reversing reverse-engineering writeup
toc: true
---

In this writeup I will describe the journey to finish this reverse engineering
challenge trying to show my complete approach in a striped binary.  

# Table of Contents
{:.no_toc}

* toc
{:toc}

# Summary Information

- Name: Segfault Labyrinth

- Author: Carl Svensson

- Category: Reversing

- Description: Be careful! One wrong turn and the whole thing comes crashing
  down

- Host: segfault-labyrinth.2022.ctfcompetition.com 

- Port: 1337

# Overview

## In-Depth Analysis

The challenge provides a binary called `challenge` that is a stripped ELF
64-bit. A stripped binary is a program without any debugging symbols. It is
normally used to reduce the size of the files and make the life of reverse
engineers ~a living hell~ more difficult (and also responsible for most
part of my headaches). First things first, checking the security settings using
`checksec`, it returns the following:

{% include gctf-2022-misc-segfault-checksec.html %}

In the output the major thing to pay attention is that the binary has writable
segments, that will be important later. Besides that it also has executable
stack (NX disabled) and no presence of canary, what is a good thing in a
challenge with "segfault" in the name. Trying to execute the binary, it shows
this:

{% include gctf-2022-misc-segfault-first-execution.html %}

There is a message of welcome and the binary hangs waiting for an input and
nothing more. Then it's ~~morbin~~ reversing time! I choose to use IDA that has
a very useful disassembly feature. With the disassembly that has no symbols to
help, I renamed a lot of variables creating a context that helped to understand
better the code. I will show some snippets and you can read the full code at the
end of this article.

The first thing the program does is to open `/dev/urandom`, and create a page
with `0x1000` bytes that is allowed to read and write content (third parameter). 

{% highlight c %}
urandom_fd = fopen("/dev/urandom", "r");
if ( urandom_fd )
{
  corridor = 10LL;
  labyrinth = mmap(0LL, 0x1000uLL, 3, 34, -1, 0LL);
  labyrinth_p = labyrinth;
{% endhighlight %}

I renamed this variable to `labyrinth` because this pointer is the entry-point
of the challenge. The second variable (with value 10) I called `corridor` that
represents the number of corridors the labyrinth will have at the end. From this
point ahead all snippets are part of a big `while` loop that when some condition
do not holds, the program ends the execution. If you check the
[original code](https://github.com/google/google-ctf/blob/master/2022/misc-segfault-labyrinth/challenge/challenge.c)
from the creator of the challenge, the code organization is very different
(modular functions, constants, etc) but we need to fight with the weapons we
have.

The next part read a byte from `urandom` and limit the value from `0` to `15`,
saving the value in `ptr[0]` (couldn't think in a better name to this variable).

{% highlight c %}
v6 = fread(ptr, 1uLL, 1uLL, urandom_fd);
random_value_0_15 = ptr[0] & 0xF;     // restrict random
LOBYTE(ptr[0]) &= 0xFu;
if ( v6 != 1 )
  break;
for ( i = 0LL; i != 16; ++i )
{
  v9 = random_value_0_15 == i;
  rand_var = rand();                  // ! srand not found in the code (?)
  door = mmap((void *)(((__int64)rand_var << 12) + 0x10000), 0x1000uLL, 3 * v9, 34, -1, 0LL);
  labyrinth_p[i] = door;
  if ( !door)
  {
    fwrite("Error: failed to allocate memory.\n", 1uLL, 0x22uLL, stderr);
    goto LABYRINTH_FAIL;
  }
  random_value_0_15 = ptr[0];         // useless?
}

labyrinth_p = (_QWORD *)labyrinth_p[LOBYTE(ptr[0])];
if ( !labyrinth_p )
  goto LABYRINTH_FAIL;
if ( !--corridor )
{
... 
{% endhighlight %}

After that, it starts a loop of 16 iterations (using `i` as the counter) where
it checks if the value of `i` is the same as the picked value in
`random_value_0_15` and save the result in `v9` (consider this a boolean (`0` or
`1`)). Then it picks a value from `rand` and save it in `rand_var`. The BIG
observation here is that `rand` wasn't seeded (keep this for later). After that
a page is created (called here `door`) where the starting address is calculated
using `rand_var` with the bits "left-shifted" 12 positions. Also the protections
of this page uses `v9` times 3 where if the value is 1, then the protection will
be the value 3 that is `PROT_READ` and `PROT_WRITE`, and if the value is 0, the
protection is `PROT_NONE` (pages cannot be accessed) (again, check the
[original](https://github.com/google/google-ctf/blob/master/2022/misc-segfault-labyrinth/challenge/challenge.c#L97)
to see how different a decompiler can be). 

Outside the loop, the only writable door will now be the entry-point to the next
corridor. Also, after that, it checks if `corridor` is zero. While not, the
`while` starts again creating a new corridor (using the entry-point as a
reference) with new 16 doors where only a single door will be writable again.
This pattern continues until the last corridor (`0`) when the `if` finally
branch in.

{% highlight c %}

if ( !--corridor )
{
  fclose(urandom_fd);
  flag_fd = fopen("flag.txt", "r");
  flag_fd_p = flag_fd;
  if ( flag_fd )
  {
    if ( fread(labyrinth_p, 1uLL, 0x1000uLL, flag_fd) )
    {
      fclose(flag_fd_p);
      shellcode = (void (__fastcall *)(_QWORD))mmap(0LL, 0x1000uLL, 7, 34, -1, 0LL);
      shellcode_p = shellcode;
      if ( shellcode )
      {
        clear_registers_size = &clear_registers_end - (_UNKNOWN *)clear_registers;
        memcpy(shellcode, clear_registers, &clear_registers_end - (_UNKNOWN *)clear_registers);
        puts("Welcome to the Segfault Labyrinth");

{% endhighlight %}

Now, after the last corridor, the flag is read to the last writable door. Then
the code allocate a page to receive our shellcode after a part that clears all
"useful" registers of the program, except for `RDI`. This `clear_registers` were 
found in `.data` and renamed properly.


{% highlight nasm %}
.data:0000000000004088 ; =============== S U B R O U T I N E ==============
.data:0000000000004088
.data:0000000000004088 clear_registers proc near
.data:0000000000004088                 xor     rax, rax
.data:000000000000408B                 xor     rcx, rcx
.data:000000000000408E                 xor     rdx, rdx
.data:0000000000004091                 xor     rbx, rbx
.data:0000000000004094                 xor     rsi, rsi
.data:0000000000004097                 xor     rsp, rsp
.data:000000000000409A                 xor     rbp, rbp
.data:000000000000409D                 xor     r8, r8
.data:00000000000040A0                 xor     r9, r9
.data:00000000000040A3                 xor     r10, r10
.data:00000000000040A6                 xor     r11, r11
.data:00000000000040A9                 xor     r12, r12
.data:00000000000040AC                 xor     r13, r13
.data:00000000000040AF                 xor     r14, r14
.data:00000000000040B2                 xor     r15, r15
.data:00000000000040B2 clear_registers endp
{% endhighlight %}

Now the program finally send the first output that is the welcome message.

{% highlight asm %}
puts("Welcome to the Segfault Labyrinth");
ptr[6] = 0xE701000015LL;
ptr[0] = 0x400000020LL;
...
v22 = 23;
v23 = ptr;
if ( prctl(38, 1LL, 0LL, 0LL, 0LL) )
{
  perror("prctl(NO_NEW_PRIVS)");
}
else if ( prctl(22, 2LL, &v22) )
{
  perror("prctl(PR_SET_SECCOMP)");
}

{% endhighlight %}

After the message, there are a lot of constant numbers set in `ptr`. I didn't 
dug further what is each number. What I did was use the tools the CTF provided
to help us that is [Google](https://www.google.com). Throwing some number there,
it returned values used in [seccomp](https://en.wikipedia.org/wiki/Seccomp)
(it provides a secure state of the calling process dealing with system calls).
Then I used `seccomp-tools` to collect the rules seccomp is applying to the
program. This is the output:

{% include gctf-2022-misc-segfault-seccomp-tools.html %}

The process has its `syscalls` restricted to `exit*`, `read`, `mmap`, `munmap`,
`fstat`, `stat` and `write`. The next instructions read a value to `ptr[0]` that
is the length of our payload.

{% highlight asm %}
    for ( j = 0LL; j <= 7; j += read(0, ptr, 8 - j) )
      ;
    if ( j == 8 )
    {
      ptr[0] %= (unsigned __int64)(4096 - clear_registers_size);
      v18 = ptr[0];
      if ( !ptr[0] )
        goto RUN_SHELLCODE_LABEL;
      do
        corridor += read(0, (char *)shellcode_p + clear_registers_size, v18 - corridor);
      while ( v18 > corridor );
      if ( ptr[0] != corridor )
      {
        fwrite("Error: failed to read code. Exiting.\n", 1uLL, 0x25uLL, stderr);
        return_code = -1;
      }
      else
      {
RUN_SHELLCODE_LABEL:
        shellcode_p(labyrinth);
      }
    }
{% endhighlight %}

Finally, our payload is read to the first position after `clear_registers` and
the shellcode is called.

## Summarizing

The main idea of the program is create a labyrinth of corridors where a single
door `Dn` in a corridor `Cm` (where `n` is a random number and `m` is the number
of the corridor) points to the beginning of the next corridor and continues so
on until it reaches the flag. The following image illustrate this behavior:

![Core idea of a representation of the labyrinth.]({{ site.url  }}/assets/images/gctf-2022-misc-segfault-labyrinth-idea.svg)

And also the program receive a payload as input that is restricted to a few
syscalls.

# Strategies and Solutions

Once we get the core idea of the binary, there are two approachable strategies
to the challenge, that I believe follows what the creator intended to do:
(1) Explore the labyrinth or (2) check each of the fixed mapped addresses.

## 1 - Explore the Labyrinth

For me, this is the clear one. When you run the program, the payload will be
combined with `clear_registers` that let us only with an address in the register
`RDI` that is the entry point of the labyrinth. To check this statement, the
image below shows an execution where the payload have multiple `\xcc` that
throws a [SIGTRAP](https://en.wikipedia.org/wiki/Signal_(IPC)#SIGTRAP) in the
debugger.

![Execution in pwndbg sending multiples `0xcc` as a payload.]({{ site.url  }}/assets/images/gctf-2022-misc-segfault-labyrinth-pwndbg-payload-breakpoint.png)

Now the target is clear, we need a payload that travels through the doors in a
corridor until we find the one that has writable permissions. To test if a
memory location is writable, we need to use one of _syscalls_ the available to
us. There are two promising ones (`stat` and `write`). In short:

- `stat` - Return information about a file, in the buffer pointed to by `statbuf`. 

- `write` - writes up to count bytes from the buffer starting at a position in
  the file referred to by the file descriptor `fd`.

In both cases, when the address is not accessible, it returns an `EFAULT`.
`EFAULT` is when you try to access or write in a bad address or an outside of
your accessible address space. To this solution, I choose to use `stat`. The
payload has three parts: `Check Doors`, `Explore Every Corridor` and `Read the
Falg`.

### Check Doors
Given a corridor, check each door (address) trying to find which one is writable. 
Since every corridor has one door that give access to the next corridor, I used
a infinite loop the breaks when the correct one is found.

```nasm
; Use r15 as the reference to explore
mov r15, rdi
; while (1)
doors_loop:
    // Use a position after our payload
    mov rdi, [r15]
    lea rsi, [rip + 0x300]
    mov rax, 4
    syscall
; compare return with EFAULT (-14)
    cmp rax, -14
    jne doors_end_loop
    add r15, 8
    jmp doors_loop
doors_end_loop:
```
This uses register `R15` as a reference to explore, copy the address to be
checked to `RDI` and call `stat` (value 4 in `RAX`). After that, check if the
returned value is equal to `EFAULT` (-14) and ends the loop when the writable
address is found. 

### Explore Every Corridor

We also know that with this approach, all corridors need to be traveled. Then
this part of the code is basically a for loop from `10` to `0`, using `EBX` as a
counter.

```asmx86
mov ebx, 10
corridors_loop:
    cmp ebx, 0
    je end_corridor_exit_labyrinth
    dec ebx

    ; SAME CODE SHOWED IN CHECK DOORS

    doors_end_loop:
    mov r15, [r15]

    jmp corridors_loop

end_corridor_exit_labyrinth:
```
After `Check Doors`, we know that the address in `R15` has as writable address,
then we can de-reference `R15` that now will points to the next corridor, until
the last one that points to the flag.

### Read the Flag

In the last part of the code, `RDI` contains the address to our desired flag,
then we use the `syscall` `WRITE` reading `0x100` bytes to `stdout` and finish
the payload calling `EXIT` with success. 

```asmx86
end_corridor_exit_labyrinth:
mov rsi, rdi
mov rdi, 1
mov rdx, 0x100
mov rax, 1
syscall
mov rax, 0x3c
xor rdi, rdi
syscall
nop
nop
nop
nop
```

In the end of the code, there are some `NOP`s (no operation) just because if the
page where payload got copied has some garbage, the last instruction could be
messed somehow.

### Execution

Getting all the code together, the following image shows how this approach
should works:

![Visualization of how the strategy works.]({{ site.url  }}/assets/images/gctf-2022-misc-segfault-labyrinth-example-animation.gif)

And running the solution (check `writeup-solver-01.py` at the end of this
article) this is the output:

{% include gctf-2022-misc-segfault-exploit-01-explore.html %}

# Final Considerations

# Codes

## IDA Disassembly

{% highlight c %}
int64 __fastcall main(int a1, char **a2, char **a3)
{
  FILE *urandom_fd;
  unsigned __int64 corridor;
  _QWORD *labyrinth_p;
  size_t v6;
  unsigned __int8 random_value_0_15;
  __int64 i;
  _BOOL4 v9;
  int rand_var;
  void *door;
  FILE *flag_fd, *flag_fd_p;
  void (__fastcall *shellcode)(_QWORD);
  void (__fastcall *shellcode_p)(_QWORD);
  signed __int64 clear_registers_size;
  unsigned __int64 j, v18;
  unsigned int return_code;
  _QWORD *labyrinth;
  __int16 v22;
  __int64 *v23, ptr[21];
  __int16 v25, v26;
  int v27;
  __int64 v28;

  if ( setvbuf(stdout, 0LL, 2, 0LL) )
  {
    fwrite("Error: failed to disable output buffering. Exiting\n", 1uLL, 0x33uLL, stderr);
    return_code = -1;
  }
  else
  {
    return_code = setvbuf(stdin, 0LL, 2, 0LL);
    if ( return_code )
    {
      fwrite("Error: failed to disable input buffering. Exiting\n", 1uLL, 0x32uLL, stderr);
      return_code = -1;
    }
    else
    {
      urandom_fd = fopen("/dev/urandom", "r");
      if ( urandom_fd )
      {
        corridor = 10LL;
        labyrinth = mmap(0LL, 0x1000uLL, 3, 34, -1, 0LL);
        labyrinth_p = labyrinth;
        while ( 1 )
        {
          v6 = fread(ptr, 1uLL, 1uLL, urandom_fd);
          random_value_0_15 = ptr[0] & 0xF;     // restrict random
          LOBYTE(ptr[0]) &= 0xFu;
          if ( v6 != 1 )
            break;
          for ( i = 0LL; i != 16; ++i )
          {
            v9 = random_value_0_15 == i;
            rand_var = rand();                  // ! srand not found in the code (?)
            door = mmap((void *)(((__int64)rand_var << 12) + 0x10000), 0x1000uLL, 3 * v9, 34, -1, 0LL);
            labyrinth_p[i] = door;
            if ( !door)
            {
              fwrite("Error: failed to allocate memory.\n", 1uLL, 0x22uLL, stderr);
              goto LABYRINTH_FAIL;
            }
            random_value_0_15 = ptr[0];         // useless?
          }
          labyrinth_p = (_QWORD *)labyrinth_p[LOBYTE(ptr[0])];
          if ( !labyrinth_p )
            goto LABYRINTH_FAIL;
          if ( !--corridor )
          {
            fclose(urandom_fd);
            flag_fd = fopen("flag.txt", "r");
            flag_fd_p = flag_fd;
            if ( flag_fd )
            {
              if ( fread(labyrinth_p, 1uLL, 0x1000uLL, flag_fd) )
              {
                fclose(flag_fd_p);
                shellcode = (void (__fastcall *)(_QWORD))mmap(0LL, 0x1000uLL, 7, 34, -1, 0LL);
                shellcode_p = shellcode;
                if ( shellcode )
                {
                  clear_registers_size = &clear_registers_end - (_UNKNOWN *)clear_registers;
                  memcpy(shellcode, clear_registers, &clear_registers_end - (_UNKNOWN *)clear_registers);
                  puts("Welcome to the Segfault Labyrinth");
                  ptr[6] = 0xE701000015LL;
                  ptr[0] = 0x400000020LL;
                  ptr[8] = 0x3C01000015LL;
                  ptr[1] = 0xC000003E00010015LL;
                  ptr[12] = 0x901000015LL;
                  ptr[4] = 0xF01000015LL;
                  ptr[14] = 0xB01000015LL;
                  ptr[5] = 0x7FFF000000000006LL;
                  ptr[7] = 0x7FFF000000000006LL;
                  ptr[9] = 0x7FFF000000000006LL;
                  ptr[11] = 0x7FFF000000000006LL;
                  ptr[13] = 0x7FFF000000000006LL;
                  ptr[15] = 0x7FFF000000000006LL;
                  ptr[16] = 0x501000015LL;
                  ptr[17] = 0x7FFF000000000006LL;
                  ptr[19] = 0x7FFF000000000006LL;
                  ptr[18] = 0x401000015LL;
                  ptr[20] = 0x101000015LL;
                  ptr[2] = 6LL;
                  ptr[3] = 32LL;
                  ptr[10] = 16777237LL;
                  v25 = 6;
                  v26 = 0;
                  v27 = 2147418112;
                  v28 = 6LL;
                  v22 = 23;
                  v23 = ptr;
                  if ( prctl(38, 1LL, 0LL, 0LL, 0LL) )
                  {
                    perror("prctl(NO_NEW_PRIVS)");
                  }
                  else if ( prctl(22, 2LL, &v22) )
                  {
                    perror("prctl(PR_SET_SECCOMP)");
                  }
                  for ( j = 0LL; j <= 7; j += read(0, ptr, 8 - j) )
                    ;
                  if ( j == 8 )
                  {
                    ptr[0] %= (unsigned __int64)(4096 - clear_registers_size);
                    v18 = ptr[0];
                    if ( !ptr[0] )
                      goto RUN_SHELLCODE_LABEL;
                    do
                      corridor += read(0, (char *)shellcode_p + clear_registers_size, v18 - corridor);
                    while ( v18 > corridor );
                    if ( ptr[0] != corridor )
                    {
                      fwrite("Error: failed to read code. Exiting.\n", 1uLL, 0x25uLL, stderr);
                      return_code = -1;
                    }
                    else
                    {
RUN_SHELLCODE_LABEL:
                      shellcode_p(labyrinth);
                    }
                  }
                  else
                  {
                    fwrite("Error: failed to read code size. Exiting.\n", 1uLL, 0x2AuLL, stderr);
                    return_code = -1;
                  }
                }
                else
                {
                  fwrite("Error: failed to allocate shellcode memory. Exiting.\n", 1uLL, 0x35uLL, stderr);
                  return_code = -1;
                }
              }
              else
              {
                fwrite("Error: failed to read flag. Exiting.\n", 1uLL, 0x25uLL, stderr);
                return_code = -1;
              }
            }
            else
            {
              fwrite("Error: failed to open flag. Exiting.\n", 1uLL, 0x25uLL, stderr);
              return_code = -1;
            }
            return return_code;
          }
        }
        fwrite("Error: failed to read random. Exiting.\n", 1uLL, 0x27uLL, stderr);
LABYRINTH_FAIL:
        fwrite("Error: failed to build labyrinth. Exiting\n", 1uLL, 0x2AuLL, stderr);
        return_code = -1;
      }
      else
      {
        fwrite("Error: failed to open urandom. Exiting\n", 1uLL, 0x27uLL, stderr);
        return_code = -1;
      }
    }
  }
  return return_code;
}
{% endhighlight %}

...

# References

- Google Capture the Flag - [https://capturetheflag.withgoogle.com/](https://capturetheflag.withgoogle.com/)
- pwntools (`checksec`) - [https://github.com/Gallopsled/pwntools](https://github.com/Gallopsled/pwntools)
- IDA - [https://hex-rays.com/ida-free/](https://hex-rays.com/ida-free/)
- Secure Computing Mode - [https://en.wikipedia.org/wiki/Seccomp](https://en.wikipedia.org/wiki/Seccomp)
- seccomp-tools - [https://github.com/david942j/seccomp-tools](https://github.com/david942j/seccomp-tools)
- stat(2) — Linux manual page - [https://man7.org/linux/man-pages/man2/lstat.2.html](https://man7.org/linux/man-pages/man2/lstat.2.html)
- write(2) — Linux manual page - [https://man7.org/linux/man-pages/man2/write.2.html](https://man7.org/linux/man-pages/man2/write.2.html)
