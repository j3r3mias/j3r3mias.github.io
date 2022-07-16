---
layout: post
title:  "Google CTF 2022 - Segfault Labyrinth"
categories: writeup
tags: ctf google-ctf reversing reverse-engineering writeup
toc: true
---

## Table of Contents
{:.no_toc}

* toc
{:toc}

## Introduction

In this writeup I will describe the journey to finish one of the challenges from 
Google CTF 2022 called Segfault Labyrinth in the ~~reversing engineering~~
miscellaneous category. The idea of this writeup is to cover mainly how to
approach and understand a striped binary.

## Summary Information

- Name: Segfault Labyrinth

- Author: [Calle “Zeta Two” Svensson](https://twitter.com/ZetaTwo)

- Category: misc

- Description: Be careful! One wrong turn and the whole thing comes crashing
  down

- Host: segfault-labyrinth.2022.ctfcompetition.com 

- Port: 1337

## Overview

### In-Depth Analysis

The challenge provides a binary called `challenge` that is a stripped `ELF
64-bit`. A stripped binary is a program without any debugging symbols. It is
normally used to reduce the size of the files and make the life of reversing
engineers ~~a living hell~~ more difficult (and also responsible for most part
of my headaches). First things first, checking the security settings using
`checksec`, it returns the following:

{% include gctf-2022-misc-segfault-checksec.html %}

In this output a big thing to pay attention is that the binary has writable
segments meaning that probably `mmap` is being called to create pages with
permissions that allow us to write and execute code. Besides that it also has
executable stack (`NX disabled`) and no presence of canary, what is a good thing
in a challenge with "*segfault*" in the name. Trying to execute the binary, this
is the output:

{% include gctf-2022-misc-segfault-first-execution.html %}

There is a message of welcome and the binary hangs waiting for an input and
nothing more. Then it's ~~morbin~~ reversing time! I chose to use IDA that has
a very useful disassembly feature. Because the binary is stripped and has no
symbols to provide any help, I renamed a lot of variables in the decompiled
code creating a context that helped me to understand better what is what. I will
show some snippets and you can read the [full
code](#04---ida-disassembly-of-the-binary) at the end of this article.

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

I renamed this variable to `labyrinth` because this pointer is the entry point
for us to the challenge. The second variable (with value 10) I called `corridor`
that represents the number of corridors the labyrinth will have after the
construction. From this point ahead all snippets are part of a big `while` loop
that when some condition do not holds, the program ends the execution. If you
check the [original
code](https://github.com/google/google-ctf/blob/master/2022/misc-segfault-labyrinth/challenge/challenge.c)
from the creator of the challenge, the code organization is very different
(modular functions, constants, etc) but we need to fight with the weapons we
have.

The next part read a byte from `urandom` and limit the value from `0` to `15`,
saving the value in `ptr[0]` (I could not decide a better name to this variable).

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
observation here is that `rand` wasn't seeded ([remember this for
later](#02---rage-against-the-random)). Thereafter a page is created (called
here `door`) where the starting address is calculated using `rand_var` with the
bits "left-shifted" 12 positions. Also the protections of this page uses `v9 * 3`
and if this result is 1, then the protection will be the value 3 that is
`PROT_READ` and `PROT_WRITE`, and if the value is 0, the protection is
`PROT_NONE` (pages cannot be accessed) (again, check the
[original](https://github.com/google/google-ctf/blob/master/2022/misc-segfault-labyrinth/challenge/challenge.c#L97)
to see how different a decompiled code can be probably (but not only) because of
flag optimizations). 

Outside the loop, the only door with writable attributes is set in
`labyrinth_p`.  This is the access point to the next corridor. Also, after
that, it checks if `corridor` is zero. While not, the loop starts again creating
a new corridor (using the current access point as a reference) with new 16 doors
where only a single door will have writable attributes again.  This pattern
continues until the last corridor (`0`) when the `if` finally branch in.

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

Now, after the last corridor, the flag is written to the last writable door.
Then the code allocates a page to receive our shellcode right after a part that
clears all "useful" registers of the program, except for `RDI`. This
`clear_registers` were found in `.data` and renamed properly.


```x86asm
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
```

Finally the program send the first output that is the welcome message.

{% highlight c %}
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
dug further what is each number. What I did was use one of the tools the CTF
provided to help us that is [Google](https://www.google.com). Throwing some
number there, it returned values used in
[seccomp](https://en.wikipedia.org/wiki/Seccomp) (it provides a secure state of
the calling process dealing with system calls).  Then I used `seccomp-tools` to
collect the rules seccomp is applying to the program. This is the output:

{% include gctf-2022-misc-segfault-seccomp-tools.html %}

The process has its `syscalls` restricted to `rt_sigreturn`, `exit_group`,
`exit`, `read`, `mmap`, `munmap`, `fstat`, `stat` and `write`. The next part of
the program read a value to `ptr` that is the length of our payload.

{% highlight c %}
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

Then our payload is written to the first position after `clear_registers` and if
everything is OK the shellcode is called.

### Summarizing

The main idea of the program is create a labyrinth of corridors where a single
door `Dn` in a corridor `Cm` (where `n` is a random number and `m` is the number
of the corridor) points to the beginning of the next corridor and continues so
on until it reaches the flag. The following image illustrate this behavior:

![Core idea of a representation of the labyrinth.]({{ site.url  }}/assets/images/gctf-2022-misc-segfault-labyrinth-idea.svg)

And also the program receive a payload as input that is restricted to a few
syscalls.

## Strategies and Solutions

Once we get the core idea of the binary, there are two approachable strategies
to the challenge, that I believe follows what the creator intended to do: (01)
Explore the Labyrinth and (02) Rage Against the Random. As a bonus, there will
be a third one that I called the (03) Lazy CTF Player.

### 01 - Explore the Labyrinth

For me, this is the clear one. When you run the program, the payload will be
combined with `clear_registers` that let us with only a single address in the
register `RDI`. This address is the entry point of the labyrinth. To check this
statement, the image below shows an execution where the payload have multiple
`INT3 (\xcc)` instruction which throws a
[SIGTRAP](https://en.wikipedia.org/wiki/Signal_(IPC)#SIGTRAP) in the debugger.

![Execution in pwndbg sending multiples `0xcc` as a payload.]({{ site.url  }}/assets/images/gctf-2022-misc-segfault-labyrinth-pwndbg-payload-breakpoint.png)

Now the target is clear, we need a payload that travels through the doors in a
corridor until we find the one that has writable permissions. To test if a
memory location is writable, we need to use one of the _syscalls_ available to
us. There are two promising ones (`stat` and `write`). In short:

- `stat` - Return information about a file, in the buffer pointed to by `statbuf`. 

- `write` - Writes up `N` bytes from the buffer starting at a position in the
  file referred to by the file descriptor `fd`.

In both cases, when the address is not accessible, it returns an `EFAULT`.
`EFAULT` is when you try to access or write in a bad address or an outside of
your accessible address space. To this solution, I choose to use `stat`. The
payload has three parts: `Check Doors`, `Explore Every Corridor` and `Read the
Flag`.

#### Check Doors
Given a corridor, check each door (address) trying to find which one is writable. 
Since every corridor has one door that give access to the next corridor, I used
a infinite loop the breaks when the correct one is found.

{% highlight nasm %}
; Use r15 as the reference to explore
mov r15, rdi
; while (1)
doors_loop:
    ; Use a position after our payload
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
{% endhighlight %}

This uses register `R15` as a reference to explore, copy the address to be
checked to `RDI` and call `stat` (value 4 in `RAX`). After that, check if the
returned value is equal to `EFAULT` (-14) and ends the loop when the writable
address is found. 

#### Explore Every Corridor

We also know that with this approach, all corridors need to be traveled. Then
this part of the code is basically a for loop from `10` to `0`, using `EBX` as a
counter.

{% highlight nasm %}
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
{% endhighlight %}

After `Check Doors`, we know that the address in `R15` has as writable address,
then we can de-reference `R15` that now will points to the next corridor, until
the last one that points to the flag.

#### Read the Flag

In the last part of the code, `RDI` contains the address to our desired flag,
then we use the `syscall` `WRITE` reading `0x100` bytes to `stdout` and finish
the payload calling `EXIT` with success. 

{% highlight nasm %}
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
{% endhighlight %}

In the end of the code, there are some `NOP`s (no operation) just because if the
page where payload got copied has some garbage, the last instruction could be
messed somehow.

#### Execution

Getting all the code together, the following image shows how this approach
should works:

![Visualization of how the strategy works.]({{ site.url  }}/assets/images/gctf-2022-misc-segfault-labyrinth-example-animation.gif)

And running the solution (check `writeup-solver-01.py` at the end of this
article) this is the output:

{% include gctf-2022-misc-segfault-exploit-01-explore.html %}

### 02 - Rage Against the Random

Like I previous mentioned in the overview, `rand_var` uses the function `rand()` 
that is not seeded in the code. [The
documentation](https://www.gnu.org/software/libc/manual/html_node/ISO-Random.html)
states that "If you call `rand` before a seed has been established with `srand`,
it uses the value `1` as a default seed." Because of that the same door will
always have the same starting address in every execution. The only difference
between different runs is because the writable doors are chosen using
`/dev/urandom`.

To take advantage of that we can use the
[`libc`](https://man7.org/linux/man-pages/man7/libc.7.html) to previous
calculate the starting address of all 160 doors (10 corridors * 16 doors per
each). The following snippet build a list with all starting addresses:

{% highlight python %}
import ctypes
libc = ctypes.cdll.LoadLibrary('libc.so.6')

doors = []
for i in range(10 * 16):
    address = (libc.rand() << 12) + 0x10000
    doors.append(hex(address))
{% endhighlight %}

Now we do not need to follow the rules of the labyrinth, and in one of the most
naive approaches we could just test every address using `stat` or `write` and
print the content every time the address is writable. This would requires a huge
payload but we can improve this strategy testing only the doors of the last
corridor where only one door has writable permissions. Then using the generated
list of doors, the construction of the payload (using python) is the following:

{% highlight python %}
for addr in doors[-16:]: 		# Last 16 doors
    door_code = f'''
mov rdi, {addr}
lea rsi, [rip + 950]
mov rax, 4
syscall
// compare return with EFAULT (-14)
cmp rax, -14
jne print_flag
'''
    payload += door_code

payload += '''
print_flag:
// write content
mov rsi, rdi
mov rdi, 1
mov rdx, 0x100
mov rax, 1
syscall
// exit
mov rax, 0x3c
xor rdi, rdi
syscall
nop
nop
nop
nop
'''
{% endhighlight %}

The loop in the code just creates a block of code that test each one of the
last 16 doors appending it to `payload`. When the right one is found, the
program jumps to the label `print_flag`, write the flag to `stdout` and exit
successfully. The [full solution](exploit-02)
can be checked at the end of this article.

### 03 - Bonus: Lazy CTF Player

This is one of that solutions you are proudly ashamed of yourself during CTFs,
but it works. Using some consolidation of the previous two solutions, this one
just guess one of the last 16 doors and repeatedly connects to the server trying
always to read the same picked address again and again until that one is
picked to contains the flag.  Since we only need to pick an address between 16
doors, `6%` of chances to hit the jackpot is very doable even if the contest
use some kind of [PoW](https://en.wikipedia.org/wiki/Proof_of_work) (Prof of
Work). Now the payload is reduced (22 bytes) to:

{% highlight nasm %}
mov rsi, GUESS_ADDRESS
mov edi, 1
mov dl, 0x40
inc eax
syscall
nop
{% endhighlight %}

Not [the most beautiful one](#03---exploit-03---lazy-ctf-player-bonus) but flag
is flag! `¯\_(ツ)_/¯`

Check the output:

{% include gctf-2022-misc-segfault-exploit-03-smart-guess.html %}

## Final Considerations

## Codes

### 01 - Exploit 01 - Explore the Labyrinth

{% gist 18750235e4273e6b591faa56af468d4c writeup-solver-01.py %}

### 02 - Exploit 02 - Rage Against the Random

{% gist 98f423599b63aa355583104c9a30cad4 writeup-solver-02.py %}

### 03 - Exploit 03 - Lazy CTF Player (Bonus)

{% gist 6808ed67b5a0e1d6b91007c394c2e085 writeup-solver-03.py %}

### 04 - IDA Disassembly of the Binary

{% gist cd019e6cc4788e062c2fd1e411b3f212 gctf-2022-misc-segfault-challenge-disasm.c %}


## References

1. [Google Capture the Flag](https://capturetheflag.withgoogle.com/)

1. [pwntools (`checksec`)](https://github.com/Gallopsled/pwntools)

1. [IDA Decompiler/Disassembler](https://hex-rays.com/ida-free/)

1. [Secure Computing Mode (Seccomp)](https://en.wikipedia.org/wiki/Seccomp)

1. [seccomp-tools](https://github.com/david942j/seccomp-tools)

1. [stat(2) — Linux manual page](https://man7.org/linux/man-pages/man2/lstat.2.html)

1. [write(2) — Linux manual page](https://man7.org/linux/man-pages/man2/write.2.html)

1. [ISO C Random Number Functions](https://www.gnu.org/software/libc/manual/html_node/ISO-Random.html)

1. [libc(7) — Linux manual page](https://man7.org/linux/man-pages/man7/libc.7.html)

1. [Proof of Work](https://en.wikipedia.org/wiki/Proof_of_work)
