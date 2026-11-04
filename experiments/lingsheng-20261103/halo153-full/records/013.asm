
/home/share/nsls_lwb/.cache/mg-opt-20261103/campaign/attempts/052-reduce-on/artifacts/liblqcd_cpu.so:     file format elf64-littleaarch64


Disassembly of section .text:

0000000000029a20 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const>:
   29a20:	a9a47bfd 	stp	x29, x30, [sp, #-448]!
   29a24:	910003fd 	mov	x29, sp
   29a28:	a90153f3 	stp	x19, x20, [sp, #16]
   29a2c:	fd003bea 	str	d10, [sp, #112]
   29a30:	f90047e0 	str	x0, [sp, #136]
   29a34:	51000460 	sub	w0, w3, #0x1
   29a38:	b9009fe3 	str	w3, [sp, #156]
   29a3c:	f9005be1 	str	x1, [sp, #176]
   29a40:	f90063e2 	str	x2, [sp, #192]
   29a44:	71002c1f 	cmp	w0, #0xb
   29a48:	54010e08 	b.hi	2bc08 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x21e8>  // b.pmore
   29a4c:	a9400021 	ldp	x1, x0, [x1]
   29a50:	b201f3e2 	mov	x2, #0xaaaaaaaaaaaaaaaa    	// #-6148914691236517206
   29a54:	93407c74 	sxtw	x20, w3
   29a58:	f2955562 	movk	x2, #0xaaab
   29a5c:	cb010000 	sub	x0, x0, x1
   29a60:	9343fc00 	asr	x0, x0, #3
   29a64:	9b027c00 	mul	x0, x0, x2
   29a68:	eb00029f 	cmp	x20, x0
   29a6c:	54010ce8 	b.hi	2bc08 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x21e8>  // b.pmore
   29a70:	f94063e1 	ldr	x1, [sp, #192]
   29a74:	a9025bf5 	stp	x21, x22, [sp, #32]
   29a78:	a9400420 	ldp	x0, x1, [x1]
   29a7c:	cb000021 	sub	x1, x1, x0
   29a80:	9343fc21 	asr	x1, x1, #3
   29a84:	9b027c21 	mul	x1, x1, x2
   29a88:	eb01029f 	cmp	x20, x1
   29a8c:	540004c8 	b.hi	29b24 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x104>  // b.pmore
   29a90:	f94047e2 	ldr	x2, [sp, #136]
   29a94:	b9409fe0 	ldr	w0, [sp, #156]
   29a98:	395ec841 	ldrb	w1, [x2, #1970]
   29a9c:	7100041f 	cmp	w0, #0x1
   29aa0:	1a9f17e0 	cset	w0, eq  // eq = none
   29aa4:	52000021 	eor	w1, w1, #0x1
   29aa8:	2a010000 	orr	w0, w0, w1
   29aac:	72001c1f 	tst	w0, #0xff
   29ab0:	540000c1 	b.ne	29ac8 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xa8>  // b.any
   29ab4:	39590440 	ldrb	w0, [x2, #1601]
   29ab8:	aa0203f3 	mov	x19, x2
   29abc:	34000060 	cbz	w0, 29ac8 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xa8>
   29ac0:	3966dc55 	ldrb	w21, [x2, #2487]
   29ac4:	34000395 	cbz	w21, 29b34 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x114>
   29ac8:	b9409fe0 	ldr	w0, [sp, #156]
   29acc:	52800314 	mov	w20, #0x18                  	// #24
   29ad0:	a90363f7 	stp	x23, x24, [sp, #48]
   29ad4:	d2800013 	mov	x19, #0x0                   	// #0
   29ad8:	f94047f5 	ldr	x21, [sp, #136]
   29adc:	f9405bf6 	ldr	x22, [sp, #176]
   29ae0:	f94063f7 	ldr	x23, [sp, #192]
   29ae4:	9bb47c14 	umull	x20, w0, w20
   29ae8:	f94002c1 	ldr	x1, [x22]
   29aec:	f94002e2 	ldr	x2, [x23]
   29af0:	aa1503e0 	mov	x0, x21
   29af4:	8b130021 	add	x1, x1, x19
   29af8:	8b130042 	add	x2, x2, x19
   29afc:	91006273 	add	x19, x19, #0x18
   29b00:	97fffd4c 	bl	29030 <NativeMG::Impl::coarse_solve(std::vector<float, lqcd_native::WorkspaceAllocator<float> > const&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&) const>
   29b04:	eb13029f 	cmp	x20, x19
   29b08:	54ffff01 	b.ne	29ae8 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xc8>  // b.any
   29b0c:	a94153f3 	ldp	x19, x20, [sp, #16]
   29b10:	a9425bf5 	ldp	x21, x22, [sp, #32]
   29b14:	a94363f7 	ldp	x23, x24, [sp, #48]
   29b18:	fd403bea 	ldr	d10, [sp, #112]
   29b1c:	a8dc7bfd 	ldp	x29, x30, [sp], #448
   29b20:	d65f03c0 	ret
   29b24:	f94063e0 	ldr	x0, [sp, #192]
   29b28:	cb010281 	sub	x1, x20, x1
   29b2c:	94000a01 	bl	2c330 <std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >::_M_default_append(unsigned long)>
   29b30:	17ffffd8 	b	29a90 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x70>
   29b34:	f0000160 	adrp	x0, 58000 <typeinfo name for lqcd::Error+0x88>
   29b38:	52800021 	mov	w1, #0x1                   	// #1
   29b3c:	910a4000 	add	x0, x0, #0x290
   29b40:	97ff8e18 	bl	d3a0 <lqcd_native::detail::setting(char const*, int)>
   29b44:	34fffc20 	cbz	w0, 29ac8 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xa8>
   29b48:	b949ba73 	ldr	w19, [x19, #2488]
   29b4c:	a90573fb 	stp	x27, x28, [sp, #80]
   29b50:	97ff6ecc 	bl	5680 <omp_get_max_threads@plt>
   29b54:	2a0003f6 	mov	w22, w0
   29b58:	b90127e0 	str	w0, [sp, #292]
   29b5c:	7100027f 	cmp	w19, #0x0
   29b60:	5400a0cc 	b.gt	2af78 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1558>
   29b64:	b9409fe1 	ldr	w1, [sp, #156]
   29b68:	52801900 	mov	w0, #0xc8                  	// #200
   29b6c:	b90123ff 	str	wzr, [sp, #288]
   29b70:	9b207c20 	smull	x0, w1, w0
   29b74:	f90083e0 	str	x0, [sp, #256]
   29b78:	97ff6db2 	bl	5240 <operator new(unsigned long)@plt>
   29b7c:	aa0003fb 	mov	x27, x0
   29b80:	f94083e0 	ldr	x0, [sp, #256]
   29b84:	8b000361 	add	x1, x27, x0
   29b88:	aa1b03e0 	mov	x0, x27
   29b8c:	f90077e1 	str	x1, [sp, #232]
   29b90:	a9007c1f 	stp	xzr, xzr, [x0]
   29b94:	a9017c1f 	stp	xzr, xzr, [x0, #16]
   29b98:	a9027c1f 	stp	xzr, xzr, [x0, #32]
   29b9c:	a9037c1f 	stp	xzr, xzr, [x0, #48]
   29ba0:	a9047c1f 	stp	xzr, xzr, [x0, #64]
   29ba4:	a9057c1f 	stp	xzr, xzr, [x0, #80]
   29ba8:	a9067c1f 	stp	xzr, xzr, [x0, #96]
   29bac:	a9077c1f 	stp	xzr, xzr, [x0, #112]
   29bb0:	a9087c1f 	stp	xzr, xzr, [x0, #128]
   29bb4:	a9097c1f 	stp	xzr, xzr, [x0, #144]
   29bb8:	91032000 	add	x0, x0, #0xc8
   29bbc:	a93dfc1f 	stp	xzr, xzr, [x0, #-40]
   29bc0:	a93efc1f 	stp	xzr, xzr, [x0, #-24]
   29bc4:	f81f801f 	stur	xzr, [x0, #-8]
   29bc8:	eb01001f 	cmp	x0, x1
   29bcc:	54fffe21 	b.ne	29b90 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x170>  // b.any
   29bd0:	d37df280 	lsl	x0, x20, #3
   29bd4:	aa0003f3 	mov	x19, x0
   29bd8:	f90073e0 	str	x0, [sp, #224]
   29bdc:	97ff6d99 	bl	5240 <operator new(unsigned long)@plt>
   29be0:	aa1303e2 	mov	x2, x19
   29be4:	52800001 	mov	w1, #0x0                   	// #0
   29be8:	a90363f7 	stp	x23, x24, [sp, #48]
   29bec:	9100c377 	add	x23, x27, #0x30
   29bf0:	6d0627e8 	stp	d8, d9, [sp, #96]
   29bf4:	0f000408 	movi	v8.2s, #0x0
   29bf8:	aa0003f6 	mov	x22, x0
   29bfc:	a9046bf9 	stp	x25, x26, [sp, #64]
   29c00:	aa0003f9 	mov	x25, x0
   29c04:	f90057e0 	str	x0, [sp, #168]
   29c08:	f90097f7 	str	x23, [sp, #296]
   29c0c:	97ff6d25 	bl	50a0 <memset@plt>
   29c10:	b9409fe0 	ldr	w0, [sp, #156]
   29c14:	52800318 	mov	w24, #0x18                  	// #24
   29c18:	d2800013 	mov	x19, #0x0                   	// #0
   29c1c:	910603fc 	add	x28, sp, #0x180
   29c20:	2f00e409 	movi	d9, #0x0
   29c24:	9bb87c18 	umull	x24, w0, w24
   29c28:	f0ffffc0 	adrp	x0, 24000 <(anonymous namespace)::coarse_gcr_fused_step(std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, double&) [clone ._omp_fn.1]+0x1a0>
   29c2c:	9128001a 	add	x26, x0, #0xa00
   29c30:	f9405be0 	ldr	x0, [sp, #176]
   29c34:	f94063e2 	ldr	x2, [sp, #192]
   29c38:	f9400001 	ldr	x1, [x0]
   29c3c:	f9400040 	ldr	x0, [x2]
   29c40:	aa1c03e2 	mov	x2, x28
   29c44:	8b130024 	add	x4, x1, x19
   29c48:	f8736823 	ldr	x3, [x1, x19]
   29c4c:	8b130000 	add	x0, x0, x19
   29c50:	f9400481 	ldr	x1, [x4, #8]
   29c54:	bd0183e8 	str	s8, [sp, #384]
   29c58:	cb030021 	sub	x1, x1, x3
   29c5c:	9342fc21 	asr	x1, x1, #2
   29c60:	940008ac 	bl	2bf10 <std::vector<float, lqcd_native::WorkspaceAllocator<float> >::_M_fill_assign(unsigned long, float const&)>
   29c64:	f9405be0 	ldr	x0, [sp, #176]
   29c68:	aa1c03e2 	mov	x2, x28
   29c6c:	f9400001 	ldr	x1, [x0]
   29c70:	aa1703e0 	mov	x0, x23
   29c74:	8b130024 	add	x4, x1, x19
   29c78:	f8736823 	ldr	x3, [x1, x19]
   29c7c:	f9400481 	ldr	x1, [x4, #8]
   29c80:	bd0183e8 	str	s8, [sp, #384]
   29c84:	cb030021 	sub	x1, x1, x3
   29c88:	9342fc21 	asr	x1, x1, #2
   29c8c:	940008a1 	bl	2bf10 <std::vector<float, lqcd_native::WorkspaceAllocator<float> >::_M_fill_assign(unsigned long, float const&)>
   29c90:	f9405be0 	ldr	x0, [sp, #176]
   29c94:	52800003 	mov	w3, #0x0                   	// #0
   29c98:	aa1c03e1 	mov	x1, x28
   29c9c:	910322f7 	add	x23, x23, #0xc8
   29ca0:	f9400002 	ldr	x2, [x0]
   29ca4:	aa1a03e0 	mov	x0, x26
   29ca8:	8b130044 	add	x4, x2, x19
   29cac:	f8736845 	ldr	x5, [x2, x19]
   29cb0:	91006273 	add	x19, x19, #0x18
   29cb4:	f9400482 	ldr	x2, [x4, #8]
   29cb8:	f900c3e4 	str	x4, [sp, #384]
   29cbc:	d2835004 	mov	x4, #0x1a80                	// #6784
   29cc0:	f2a000c4 	movk	x4, #0x6, lsl #16
   29cc4:	fd00c7e9 	str	d9, [sp, #392]
   29cc8:	cb050042 	sub	x2, x2, x5
   29ccc:	eb04005f 	cmp	x2, x4
   29cd0:	1a9f87e2 	cset	w2, ls  // ls = plast
   29cd4:	97ff6e1f 	bl	5550 <GOMP_parallel@plt>
   29cd8:	fd40c7e0 	ldr	d0, [sp, #392]
   29cdc:	fc008720 	str	d0, [x25], #8
   29ce0:	eb18027f 	cmp	x19, x24
   29ce4:	54fffa61 	b.ne	29c30 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x210>  // b.any
   29ce8:	d00002a0 	adrp	x0, 7f000 <__FRAME_END__+0x1ea64>
   29cec:	f9475800 	ldr	x0, [x0, #3760]
   29cf0:	b9400000 	ldr	w0, [x0]
   29cf4:	7100041f 	cmp	w0, #0x1
   29cf8:	5400964c 	b.gt	2afc0 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x15a0>
   29cfc:	aa1b03f3 	mov	x19, x27
   29d00:	d2800017 	mov	x23, #0x0                   	// #0
   29d04:	d503201f 	nop
   29d08:	fd4002c0 	ldr	d0, [x22]
   29d0c:	1e602008 	fcmp	d0, #0.0
   29d10:	54000065 	b.pl	29d1c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x2fc>  // b.nfrst
   29d14:	97ff6eb3 	bl	57e0 <sqrt@plt>
   29d18:	14000002 	b	29d20 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x300>
   29d1c:	1e61c000 	fsqrt	d0, d0
   29d20:	1e602008 	fcmp	d0, #0.0
   29d24:	fd005660 	str	d0, [x19, #168]
   29d28:	1a9f17e1 	cset	w1, eq  // eq = none
   29d2c:	1a9f07e0 	cset	w0, ne  // ne = any
   29d30:	39031261 	strb	w1, [x19, #196]
   29d34:	2a0002b5 	orr	w21, w21, w0
   29d38:	54000140 	b.eq	29d60 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x340>  // b.none
   29d3c:	f9405be0 	ldr	x0, [sp, #176]
   29d40:	aa1303e2 	mov	x2, x19
   29d44:	f9400001 	ldr	x1, [x0]
   29d48:	f94047e0 	ldr	x0, [sp, #136]
   29d4c:	8b170021 	add	x1, x1, x23
   29d50:	97fff8f4 	bl	28120 <NativeMG::Impl::coarse_reduced_rhs(std::vector<float, lqcd_native::WorkspaceAllocator<float> > const&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&) const>
   29d54:	aa1303e1 	mov	x1, x19
   29d58:	91006260 	add	x0, x19, #0x18
   29d5c:	97fff291 	bl	267a0 <std::vector<float, lqcd_native::WorkspaceAllocator<float> >::operator=(std::vector<float, lqcd_native::WorkspaceAllocator<float> > const&) [clone .isra.0]>
   29d60:	910062f7 	add	x23, x23, #0x18
   29d64:	910022d6 	add	x22, x22, #0x8
   29d68:	91032273 	add	x19, x19, #0xc8
   29d6c:	eb1802ff 	cmp	x23, x24
   29d70:	54fffcc1 	b.ne	29d08 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x2e8>  // b.any
   29d74:	3400ab95 	cbz	w21, 2b2e4 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x18c4>
   29d78:	f94057e0 	ldr	x0, [sp, #168]
   29d7c:	f94073e2 	ldr	x2, [sp, #224]
   29d80:	52800001 	mov	w1, #0x0                   	// #0
   29d84:	97ff6cc7 	bl	50a0 <memset@plt>
   29d88:	39431360 	ldrb	w0, [x27, #196]
   29d8c:	34009960 	cbz	w0, 2b0b8 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1698>
   29d90:	39463360 	ldrb	w0, [x27, #396]
   29d94:	91032361 	add	x1, x27, #0xc8
   29d98:	f9009be1 	str	x1, [sp, #304]
   29d9c:	340096a0 	cbz	w0, 2b070 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1650>
   29da0:	b9409fe0 	ldr	w0, [sp, #156]
   29da4:	7100081f 	cmp	w0, #0x2
   29da8:	54000860 	b.eq	29eb4 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x494>  // b.none
   29dac:	39495360 	ldrb	w0, [x27, #596]
   29db0:	34009a80 	cbz	w0, 2b100 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x16e0>
   29db4:	b9409fe0 	ldr	w0, [sp, #156]
   29db8:	71000c1f 	cmp	w0, #0x3
   29dbc:	540007c0 	b.eq	29eb4 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x494>  // b.none
   29dc0:	394c7360 	ldrb	w0, [x27, #796]
   29dc4:	3400a6a0 	cbz	w0, 2b298 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1878>
   29dc8:	b9409fe0 	ldr	w0, [sp, #156]
   29dcc:	7100101f 	cmp	w0, #0x4
   29dd0:	54000720 	b.eq	29eb4 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x494>  // b.none
   29dd4:	394f9360 	ldrb	w0, [x27, #996]
   29dd8:	3400c820 	cbz	w0, 2b6dc <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1cbc>
   29ddc:	b9409fe0 	ldr	w0, [sp, #156]
   29de0:	7100141f 	cmp	w0, #0x5
   29de4:	54000680 	b.eq	29eb4 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x494>  // b.none
   29de8:	3952b361 	ldrb	w1, [x27, #1196]
   29dec:	91100360 	add	x0, x27, #0x400
   29df0:	3400c9c1 	cbz	w1, 2b728 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1d08>
   29df4:	b9409fe0 	ldr	w0, [sp, #156]
   29df8:	7100181f 	cmp	w0, #0x6
   29dfc:	540005c0 	b.eq	29eb4 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x494>  // b.none
   29e00:	3955d360 	ldrb	w0, [x27, #1396]
   29e04:	3400d2c0 	cbz	w0, 2b85c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1e3c>
   29e08:	b9409fe0 	ldr	w0, [sp, #156]
   29e0c:	71001c1f 	cmp	w0, #0x7
   29e10:	54000520 	b.eq	29eb4 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x494>  // b.none
   29e14:	3958f360 	ldrb	w0, [x27, #1596]
   29e18:	3400dd00 	cbz	w0, 2b9b8 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1f98>
   29e1c:	b9409fe0 	ldr	w0, [sp, #156]
   29e20:	7100201f 	cmp	w0, #0x8
   29e24:	54000480 	b.eq	29eb4 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x494>  // b.none
   29e28:	395c1360 	ldrb	w0, [x27, #1796]
   29e2c:	3400da00 	cbz	w0, 2b96c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1f4c>
   29e30:	b9409fe0 	ldr	w0, [sp, #156]
   29e34:	7100241f 	cmp	w0, #0x9
   29e38:	540003e0 	b.eq	29eb4 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x494>  // b.none
   29e3c:	395f3360 	ldrb	w0, [x27, #1996]
   29e40:	3400d700 	cbz	w0, 2b920 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1f00>
   29e44:	b9409fe0 	ldr	w0, [sp, #156]
   29e48:	7100281f 	cmp	w0, #0xa
   29e4c:	54000340 	b.eq	29eb4 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x494>  // b.none
   29e50:	39625360 	ldrb	w0, [x27, #2196]
   29e54:	3400e280 	cbz	w0, 2baa4 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x2084>
   29e58:	b9409fe0 	ldr	w0, [sp, #156]
   29e5c:	71002c1f 	cmp	w0, #0xb
   29e60:	540002a0 	b.eq	29eb4 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x494>  // b.none
   29e64:	39657360 	ldrb	w0, [x27, #2396]
   29e68:	35000260 	cbnz	w0, 29eb4 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x494>
   29e6c:	f9445b65 	ldr	x5, [x27, #2224]
   29e70:	f9445f62 	ldr	x2, [x27, #2232]
   29e74:	d2835004 	mov	x4, #0x1a80                	// #6784
   29e78:	9122c360 	add	x0, x27, #0x8b0
   29e7c:	f2a000c4 	movk	x4, #0x6, lsl #16
   29e80:	f900c3e0 	str	x0, [sp, #384]
   29e84:	f0ffffc0 	adrp	x0, 24000 <(anonymous namespace)::coarse_gcr_fused_step(std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, double&) [clone ._omp_fn.1]+0x1a0>
   29e88:	52800003 	mov	w3, #0x0                   	// #0
   29e8c:	91280000 	add	x0, x0, #0xa00
   29e90:	aa1c03e1 	mov	x1, x28
   29e94:	f900c7ff 	str	xzr, [sp, #392]
   29e98:	cb050042 	sub	x2, x2, x5
   29e9c:	eb04005f 	cmp	x2, x4
   29ea0:	1a9f87e2 	cset	w2, ls  // ls = plast
   29ea4:	97ff6dab 	bl	5550 <GOMP_parallel@plt>
   29ea8:	fd40c7e0 	ldr	d0, [sp, #392]
   29eac:	f94057e0 	ldr	x0, [sp, #168]
   29eb0:	fd002c00 	str	d0, [x0, #88]
   29eb4:	d00002a0 	adrp	x0, 7f000 <__FRAME_END__+0x1ea64>
   29eb8:	f9475800 	ldr	x0, [x0, #3760]
   29ebc:	b9400000 	ldr	w0, [x0]
   29ec0:	7100041f 	cmp	w0, #0x1
   29ec4:	5400898c 	b.gt	2aff4 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x15d4>
   29ec8:	f94057e0 	ldr	x0, [sp, #168]
   29ecc:	fd400000 	ldr	d0, [x0]
   29ed0:	1e602008 	fcmp	d0, #0.0
   29ed4:	540000a5 	b.pl	29ee8 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x4c8>  // b.nfrst
   29ed8:	97ff6e42 	bl	57e0 <sqrt@plt>
   29edc:	1e604001 	fmov	d1, d0
   29ee0:	f94057e0 	ldr	x0, [sp, #168]
   29ee4:	14000002 	b	29eec <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x4cc>
   29ee8:	1e61c001 	fsqrt	d1, d0
   29eec:	fd400400 	ldr	d0, [x0, #8]
   29ef0:	fd005b61 	str	d1, [x27, #176]
   29ef4:	1e602008 	fcmp	d0, #0.0
   29ef8:	54000065 	b.pl	29f04 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x4e4>  // b.nfrst
   29efc:	97ff6e39 	bl	57e0 <sqrt@plt>
   29f00:	14000002 	b	29f08 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x4e8>
   29f04:	1e61c000 	fsqrt	d0, d0
   29f08:	b9409fe0 	ldr	w0, [sp, #156]
   29f0c:	fd00bf60 	str	d0, [x27, #376]
   29f10:	7100081f 	cmp	w0, #0x2
   29f14:	54000b40 	b.eq	2a07c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x65c>  // b.none
   29f18:	f94057e0 	ldr	x0, [sp, #168]
   29f1c:	fd400800 	ldr	d0, [x0, #16]
   29f20:	1e602008 	fcmp	d0, #0.0
   29f24:	54000065 	b.pl	29f30 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x510>  // b.nfrst
   29f28:	97ff6e2e 	bl	57e0 <sqrt@plt>
   29f2c:	14000002 	b	29f34 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x514>
   29f30:	1e61c000 	fsqrt	d0, d0
   29f34:	b9409fe0 	ldr	w0, [sp, #156]
   29f38:	fd012360 	str	d0, [x27, #576]
   29f3c:	71000c1f 	cmp	w0, #0x3
   29f40:	540009e0 	b.eq	2a07c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x65c>  // b.none
   29f44:	f94057e0 	ldr	x0, [sp, #168]
   29f48:	fd400c00 	ldr	d0, [x0, #24]
   29f4c:	1e602008 	fcmp	d0, #0.0
   29f50:	54009285 	b.pl	2b1a0 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1780>  // b.nfrst
   29f54:	97ff6e23 	bl	57e0 <sqrt@plt>
   29f58:	b9409fe0 	ldr	w0, [sp, #156]
   29f5c:	fd018760 	str	d0, [x27, #776]
   29f60:	7100101f 	cmp	w0, #0x4
   29f64:	540008c0 	b.eq	2a07c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x65c>  // b.none
   29f68:	f94057e0 	ldr	x0, [sp, #168]
   29f6c:	fd401000 	ldr	d0, [x0, #32]
   29f70:	1e602008 	fcmp	d0, #0.0
   29f74:	540091a5 	b.pl	2b1a8 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1788>  // b.nfrst
   29f78:	97ff6e1a 	bl	57e0 <sqrt@plt>
   29f7c:	b9409fe0 	ldr	w0, [sp, #156]
   29f80:	fd01eb60 	str	d0, [x27, #976]
   29f84:	7100141f 	cmp	w0, #0x5
   29f88:	540007a0 	b.eq	2a07c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x65c>  // b.none
   29f8c:	f94057e0 	ldr	x0, [sp, #168]
   29f90:	fd401400 	ldr	d0, [x0, #40]
   29f94:	1e602008 	fcmp	d0, #0.0
   29f98:	540090c5 	b.pl	2b1b0 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1790>  // b.nfrst
   29f9c:	97ff6e11 	bl	57e0 <sqrt@plt>
   29fa0:	b9409fe0 	ldr	w0, [sp, #156]
   29fa4:	fd024f60 	str	d0, [x27, #1176]
   29fa8:	7100181f 	cmp	w0, #0x6
   29fac:	54000680 	b.eq	2a07c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x65c>  // b.none
   29fb0:	f94057e0 	ldr	x0, [sp, #168]
   29fb4:	fd401800 	ldr	d0, [x0, #48]
   29fb8:	1e602008 	fcmp	d0, #0.0
   29fbc:	540092c5 	b.pl	2b214 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x17f4>  // b.nfrst
   29fc0:	97ff6e08 	bl	57e0 <sqrt@plt>
   29fc4:	b9409fe0 	ldr	w0, [sp, #156]
   29fc8:	fd02b360 	str	d0, [x27, #1376]
   29fcc:	71001c1f 	cmp	w0, #0x7
   29fd0:	54000560 	b.eq	2a07c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x65c>  // b.none
   29fd4:	f94057e0 	ldr	x0, [sp, #168]
   29fd8:	fd401c00 	ldr	d0, [x0, #56]
   29fdc:	1e602008 	fcmp	d0, #0.0
   29fe0:	54009365 	b.pl	2b24c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x182c>  // b.nfrst
   29fe4:	97ff6dff 	bl	57e0 <sqrt@plt>
   29fe8:	b9409fe0 	ldr	w0, [sp, #156]
   29fec:	fd031760 	str	d0, [x27, #1576]
   29ff0:	7100201f 	cmp	w0, #0x8
   29ff4:	54000440 	b.eq	2a07c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x65c>  // b.none
   29ff8:	f94057e0 	ldr	x0, [sp, #168]
   29ffc:	fd402000 	ldr	d0, [x0, #64]
   2a000:	1e602008 	fcmp	d0, #0.0
   2a004:	54009205 	b.pl	2b244 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1824>  // b.nfrst
   2a008:	97ff6df6 	bl	57e0 <sqrt@plt>
   2a00c:	b9409fe0 	ldr	w0, [sp, #156]
   2a010:	fd037b60 	str	d0, [x27, #1776]
   2a014:	7100241f 	cmp	w0, #0x9
   2a018:	54000320 	b.eq	2a07c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x65c>  // b.none
   2a01c:	f94057e0 	ldr	x0, [sp, #168]
   2a020:	fd402400 	ldr	d0, [x0, #72]
   2a024:	1e602008 	fcmp	d0, #0.0
   2a028:	54009265 	b.pl	2b274 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1854>  // b.nfrst
   2a02c:	97ff6ded 	bl	57e0 <sqrt@plt>
   2a030:	b9409fe0 	ldr	w0, [sp, #156]
   2a034:	fd03df60 	str	d0, [x27, #1976]
   2a038:	7100281f 	cmp	w0, #0xa
   2a03c:	54000200 	b.eq	2a07c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x65c>  // b.none
   2a040:	f94057e0 	ldr	x0, [sp, #168]
   2a044:	fd402800 	ldr	d0, [x0, #80]
   2a048:	1e602008 	fcmp	d0, #0.0
   2a04c:	54009185 	b.pl	2b27c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x185c>  // b.nfrst
   2a050:	97ff6de4 	bl	57e0 <sqrt@plt>
   2a054:	b9409fe0 	ldr	w0, [sp, #156]
   2a058:	fd044360 	str	d0, [x27, #2176]
   2a05c:	71002c1f 	cmp	w0, #0xb
   2a060:	540000e0 	b.eq	2a07c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x65c>  // b.none
   2a064:	f94057e0 	ldr	x0, [sp, #168]
   2a068:	fd402c00 	ldr	d0, [x0, #88]
   2a06c:	1e602008 	fcmp	d0, #0.0
   2a070:	5400af45 	b.pl	2b658 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1c38>  // b.nfrst
   2a074:	97ff6ddb 	bl	57e0 <sqrt@plt>
   2a078:	fd04a760 	str	d0, [x27, #2376]
   2a07c:	910543e0 	add	x0, sp, #0x150
   2a080:	aa1403e1 	mov	x1, x20
   2a084:	a9157fff 	stp	xzr, xzr, [sp, #336]
   2a088:	a9167fff 	stp	xzr, xzr, [sp, #352]
   2a08c:	f90087e0 	str	x0, [sp, #264]
   2a090:	a9177fff 	stp	xzr, xzr, [sp, #368]
   2a094:	97ff6cef 	bl	5450 <std::vector<int, std::allocator<int> >::reserve(unsigned long)@plt>
   2a098:	9105a3e0 	add	x0, sp, #0x168
   2a09c:	aa1403e1 	mov	x1, x20
   2a0a0:	f9008fe0 	str	x0, [sp, #280]
   2a0a4:	97ff6ceb 	bl	5450 <std::vector<int, std::allocator<int> >::reserve(unsigned long)@plt>
   2a0a8:	b9409ff5 	ldr	w21, [sp, #156]
   2a0ac:	531f7ab3 	lsl	w19, w21, #1
   2a0b0:	937d7e74 	sbfiz	x20, x19, #3, #32
   2a0b4:	aa1403e0 	mov	x0, x20
   2a0b8:	f9005ff4 	str	x20, [sp, #184]
   2a0bc:	97ff6c61 	bl	5240 <operator new(unsigned long)@plt>
   2a0c0:	aa1403e2 	mov	x2, x20
   2a0c4:	52800001 	mov	w1, #0x0                   	// #0
   2a0c8:	aa0003fa 	mov	x26, x0
   2a0cc:	0b150273 	add	w19, w19, w21
   2a0d0:	97ff6bf4 	bl	50a0 <memset@plt>
   2a0d4:	937d7e73 	sbfiz	x19, x19, #3, #32
   2a0d8:	aa1303e0 	mov	x0, x19
   2a0dc:	f9007bf3 	str	x19, [sp, #240]
   2a0e0:	97ff6c58 	bl	5240 <operator new(unsigned long)@plt>
   2a0e4:	aa1303e2 	mov	x2, x19
   2a0e8:	52800001 	mov	w1, #0x0                   	// #0
   2a0ec:	f90067e0 	str	x0, [sp, #200]
   2a0f0:	97ff6bec 	bl	50a0 <memset@plt>
   2a0f4:	f94047e0 	ldr	x0, [sp, #136]
   2a0f8:	b94ad800 	ldr	w0, [x0, #2776]
   2a0fc:	7100001f 	cmp	w0, #0x0
   2a100:	52800040 	mov	w0, #0x2                   	// #2
   2a104:	b900dbe0 	str	w0, [sp, #216]
   2a108:	5400370d 	b.le	2a7e8 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xdc8>
   2a10c:	d0000160 	adrp	x0, 58000 <typeinfo name for lqcd::Error+0x88>
   2a110:	b900dfff 	str	wzr, [sp, #220]
   2a114:	fd448c0a 	ldr	d10, [x0, #2328]
   2a118:	d3438a80 	ubfx	x0, x20, #3, #32
   2a11c:	f9006be0 	str	x0, [sp, #208]
   2a120:	d3438a60 	ubfx	x0, x19, #3, #32
   2a124:	f9008be0 	str	x0, [sp, #272]
   2a128:	f94073e0 	ldr	x0, [sp, #224]
   2a12c:	d3438800 	ubfx	x0, x0, #3, #32
   2a130:	f9007fe0 	str	x0, [sp, #248]
   2a134:	d503201f 	nop
   2a138:	a95503f3 	ldp	x19, x0, [sp, #336]
   2a13c:	eb00027f 	cmp	x19, x0
   2a140:	54000040 	b.eq	2a148 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x728>  // b.none
   2a144:	f900aff3 	str	x19, [sp, #344]
   2a148:	d0ffffc1 	adrp	x1, 24000 <(anonymous namespace)::coarse_gcr_fused_step(std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, double&) [clone ._omp_fn.1]+0x1a0>
   2a14c:	b201f3f8 	mov	x24, #0xaaaaaaaaaaaaaaaa    	// #-6148914691236517206
   2a150:	52800000 	mov	w0, #0x0                   	// #0
   2a154:	f90053ff 	str	xzr, [sp, #160]
   2a158:	912b4037 	add	x23, x1, #0xad0
   2a15c:	52801915 	mov	w21, #0xc8                  	// #200
   2a160:	f2955578 	movk	x24, #0xaaab
   2a164:	b9014fff 	str	wzr, [sp, #332]
   2a168:	910533f9 	add	x25, sp, #0x14c
   2a16c:	d503201f 	nop
   2a170:	9b356c14 	smaddl	x20, w0, w21, x27
   2a174:	39431281 	ldrb	w1, [x20, #196]
   2a178:	350000e1 	cbnz	w1, 2a194 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x774>
   2a17c:	f94047e1 	ldr	x1, [sp, #136]
   2a180:	6d4a8682 	ldp	d2, d1, [x20, #168]
   2a184:	fd44e420 	ldr	d0, [x1, #2504]
   2a188:	1e620800 	fmul	d0, d0, d2
   2a18c:	1e602030 	fcmpe	d1, d0
   2a190:	54005caa 	b.ge	2ad24 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1304>  // b.tcont
   2a194:	b9409fe1 	ldr	w1, [sp, #156]
   2a198:	11000400 	add	w0, w0, #0x1
   2a19c:	b9014fe0 	str	w0, [sp, #332]
   2a1a0:	6b00003f 	cmp	w1, w0
   2a1a4:	54fffe6c 	b.gt	2a170 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x750>
   2a1a8:	f940abf4 	ldr	x20, [sp, #336]
   2a1ac:	eb13029f 	cmp	x20, x19
   2a1b0:	540031c0 	b.eq	2a7e8 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xdc8>  // b.none
   2a1b4:	f94053e0 	ldr	x0, [sp, #160]
   2a1b8:	b4008660 	cbz	x0, 2b284 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1864>
   2a1bc:	b940dbe1 	ldr	w1, [sp, #216]
   2a1c0:	d0ffffc0 	adrp	x0, 24000 <(anonymous namespace)::coarse_gcr_fused_step(std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, double&) [clone ._omp_fn.1]+0x1a0>
   2a1c4:	d2800016 	mov	x22, #0x0                   	// #0
   2a1c8:	d2800015 	mov	x21, #0x0                   	// #0
   2a1cc:	91178000 	add	x0, x0, #0x5e0
   2a1d0:	f90043e0 	str	x0, [sp, #128]
   2a1d4:	11000421 	add	w1, w1, #0x1
   2a1d8:	b90093e1 	str	w1, [sp, #144]
   2a1dc:	d503201f 	nop
   2a1e0:	f9405fe2 	ldr	x2, [sp, #184]
   2a1e4:	52800001 	mov	w1, #0x0                   	// #0
   2a1e8:	aa1a03e0 	mov	x0, x26
   2a1ec:	97ff6bad 	bl	50a0 <memset@plt>
   2a1f0:	eb13029f 	cmp	x20, x19
   2a1f4:	540063a0 	b.eq	2ae68 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1448>  // b.none
   2a1f8:	aa1c03e0 	mov	x0, x28
   2a1fc:	b201f3f8 	mov	x24, #0xaaaaaaaaaaaaaaaa    	// #-6148914691236517206
   2a200:	aa1603fc 	mov	x28, x22
   2a204:	52801919 	mov	w25, #0xc8                  	// #200
   2a208:	aa1503f6 	mov	x22, x21
   2a20c:	f2955578 	movk	x24, #0xaaab
   2a210:	aa1303f5 	mov	x21, x19
   2a214:	aa0003f3 	mov	x19, x0
   2a218:	b9400297 	ldr	w23, [x20]
   2a21c:	9b396ee2 	smaddl	x2, w23, w25, x27
   2a220:	a9490043 	ldp	x3, x0, [x2, #144]
   2a224:	cb030000 	sub	x0, x0, x3
   2a228:	9343fc00 	asr	x0, x0, #3
   2a22c:	9b187c00 	mul	x0, x0, x24
   2a230:	eb16001f 	cmp	x0, x22
   2a234:	540002a9 	b.ls	2a288 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x868>  // b.plast
   2a238:	8b1c0060 	add	x0, x3, x28
   2a23c:	f87c6865 	ldr	x5, [x3, x28]
   2a240:	91018042 	add	x2, x2, #0x60
   2a244:	52800003 	mov	w3, #0x0                   	// #0
   2a248:	f9400404 	ldr	x4, [x0, #8]
   2a24c:	a9180be0 	stp	x0, x2, [sp, #384]
   2a250:	aa1303e1 	mov	x1, x19
   2a254:	531f7af7 	lsl	w23, w23, #1
   2a258:	f94043e0 	ldr	x0, [sp, #128]
   2a25c:	a9197fff 	stp	xzr, xzr, [sp, #400]
   2a260:	937d7ef7 	sbfiz	x23, x23, #3, #32
   2a264:	cb050082 	sub	x2, x4, x5
   2a268:	d2835004 	mov	x4, #0x1a80                	// #6784
   2a26c:	f2a000c4 	movk	x4, #0x6, lsl #16
   2a270:	eb04005f 	cmp	x2, x4
   2a274:	1a9f87e2 	cset	w2, ls  // ls = plast
   2a278:	97ff6cb6 	bl	5550 <GOMP_parallel@plt>
   2a27c:	3dc067e0 	ldr	q0, [sp, #400]
   2a280:	6e004000 	ext	v0.16b, v0.16b, v0.16b, #8
   2a284:	3cb76b40 	str	q0, [x26, x23]
   2a288:	91001294 	add	x20, x20, #0x4
   2a28c:	eb15029f 	cmp	x20, x21
   2a290:	54fffc41 	b.ne	2a218 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x7f8>  // b.any
   2a294:	b00002a0 	adrp	x0, 7f000 <__FRAME_END__+0x1ea64>
   2a298:	aa1603f5 	mov	x21, x22
   2a29c:	aa1c03f6 	mov	x22, x28
   2a2a0:	f9475800 	ldr	x0, [x0, #3760]
   2a2a4:	aa1303fc 	mov	x28, x19
   2a2a8:	b9400000 	ldr	w0, [x0]
   2a2ac:	7100041f 	cmp	w0, #0x1
   2a2b0:	5400516c 	b.gt	2acdc <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x12bc>
   2a2b4:	b94093e0 	ldr	w0, [sp, #144]
   2a2b8:	a9555ff3 	ldp	x19, x23, [sp, #336]
   2a2bc:	b900dbe0 	str	w0, [sp, #216]
   2a2c0:	eb1302ff 	cmp	x23, x19
   2a2c4:	540052c0 	b.eq	2ad1c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x12fc>  // b.none
   2a2c8:	b201f3f9 	mov	x25, #0xaaaaaaaaaaaaaaaa    	// #-6148914691236517206
   2a2cc:	52801918 	mov	w24, #0xc8                  	// #200
   2a2d0:	f2955579 	movk	x25, #0xaaab
   2a2d4:	d503201f 	nop
   2a2d8:	b9400262 	ldr	w2, [x19]
   2a2dc:	9b386c54 	smaddl	x20, w2, w24, x27
   2a2e0:	a9490281 	ldp	x1, x0, [x20, #144]
   2a2e4:	cb010000 	sub	x0, x0, x1
   2a2e8:	9343fc00 	asr	x0, x0, #3
   2a2ec:	9b197c00 	mul	x0, x0, x25
   2a2f0:	eb15001f 	cmp	x0, x21
   2a2f4:	54000249 	b.ls	2a33c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x91c>  // b.plast
   2a2f8:	531f7842 	lsl	w2, w2, #1
   2a2fc:	11000440 	add	w0, w2, #0x1
   2a300:	fc62db49 	ldr	d9, [x26, w2, sxtw #3]
   2a304:	8b160021 	add	x1, x1, x22
   2a308:	fc60db48 	ldr	d8, [x26, w0, sxtw #3]
   2a30c:	91018280 	add	x0, x20, #0x60
   2a310:	1e614129 	fneg	d9, d9
   2a314:	1e614108 	fneg	d8, d8
   2a318:	1e604120 	fmov	d0, d9
   2a31c:	1e604101 	fmov	d1, d8
   2a320:	97ff8d04 	bl	d730 <lqcd_native::detail::coarse_axpy(std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::complex<double>, std::vector<float, lqcd_native::WorkspaceAllocator<float> > const&)>
   2a324:	f9403e81 	ldr	x1, [x20, #120]
   2a328:	1e604120 	fmov	d0, d9
   2a32c:	91012280 	add	x0, x20, #0x48
   2a330:	1e604101 	fmov	d1, d8
   2a334:	8b160021 	add	x1, x1, x22
   2a338:	97ff8cfe 	bl	d730 <lqcd_native::detail::coarse_axpy(std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::complex<double>, std::vector<float, lqcd_native::WorkspaceAllocator<float> > const&)>
   2a33c:	91001273 	add	x19, x19, #0x4
   2a340:	eb1302ff 	cmp	x23, x19
   2a344:	54fffca1 	b.ne	2a2d8 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x8b8>  // b.any
   2a348:	a9554ff4 	ldp	x20, x19, [sp, #336]
   2a34c:	b94093e0 	ldr	w0, [sp, #144]
   2a350:	910006b5 	add	x21, x21, #0x1
   2a354:	910062d6 	add	x22, x22, #0x18
   2a358:	11000400 	add	w0, w0, #0x1
   2a35c:	b90093e0 	str	w0, [sp, #144]
   2a360:	f94053e0 	ldr	x0, [sp, #160]
   2a364:	eb0002bf 	cmp	x21, x0
   2a368:	54fff3c1 	b.ne	2a1e0 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x7c0>  // b.any
   2a36c:	f94067e0 	ldr	x0, [sp, #200]
   2a370:	f9407be2 	ldr	x2, [sp, #240]
   2a374:	52800001 	mov	w1, #0x0                   	// #0
   2a378:	97ff6b4a 	bl	50a0 <memset@plt>
   2a37c:	eb14027f 	cmp	x19, x20
   2a380:	54000480 	b.eq	2a410 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x9f0>  // b.none
   2a384:	f94067f8 	ldr	x24, [sp, #200]
   2a388:	d0ffffd7 	adrp	x23, 24000 <(anonymous namespace)::coarse_gcr_fused_step(std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, double&) [clone ._omp_fn.1]+0x1a0>
   2a38c:	aa1403f5 	mov	x21, x20
   2a390:	2f00e408 	movi	d8, #0x0
   2a394:	52801914 	mov	w20, #0xc8                  	// #200
   2a398:	911bc2f7 	add	x23, x23, #0x6f0
   2a39c:	d503201f 	nop
   2a3a0:	b84046b6 	ldr	w22, [x21], #4
   2a3a4:	aa1c03e1 	mov	x1, x28
   2a3a8:	aa1703e0 	mov	x0, x23
   2a3ac:	52800003 	mov	w3, #0x0                   	// #0
   2a3b0:	6d1923e8 	stp	d8, d8, [sp, #400]
   2a3b4:	fd00d3e8 	str	d8, [sp, #416]
   2a3b8:	9b346ec2 	smaddl	x2, w22, w20, x27
   2a3bc:	0b1606d6 	add	w22, w22, w22, lsl #1
   2a3c0:	f9403046 	ldr	x6, [x2, #96]
   2a3c4:	f9403444 	ldr	x4, [x2, #104]
   2a3c8:	91018045 	add	x5, x2, #0x60
   2a3cc:	91006042 	add	x2, x2, #0x18
   2a3d0:	a9180be5 	stp	x5, x2, [sp, #384]
   2a3d4:	8b36cf16 	add	x22, x24, w22, sxtw #3
   2a3d8:	cb060082 	sub	x2, x4, x6
   2a3dc:	d2835004 	mov	x4, #0x1a80                	// #6784
   2a3e0:	f2a000c4 	movk	x4, #0x6, lsl #16
   2a3e4:	eb04005f 	cmp	x2, x4
   2a3e8:	1a9f87e2 	cset	w2, ls  // ls = plast
   2a3ec:	97ff6c59 	bl	5550 <GOMP_parallel@plt>
   2a3f0:	6d5987e0 	ldp	d0, d1, [sp, #408]
   2a3f4:	f9400b82 	ldr	x2, [x28, #16]
   2a3f8:	f9000ac2 	str	x2, [x22, #16]
   2a3fc:	6d1803e1 	stp	d1, d0, [sp, #384]
   2a400:	a9400780 	ldp	x0, x1, [x28]
   2a404:	a90006c0 	stp	x0, x1, [x22]
   2a408:	eb1302bf 	cmp	x21, x19
   2a40c:	54fffca1 	b.ne	2a3a0 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x980>  // b.any
   2a410:	b00002a0 	adrp	x0, 7f000 <__FRAME_END__+0x1ea64>
   2a414:	f9475800 	ldr	x0, [x0, #3760]
   2a418:	b9400000 	ldr	w0, [x0]
   2a41c:	7100041f 	cmp	w0, #0x1
   2a420:	540055cc 	b.gt	2aed8 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x14b8>
   2a424:	f94057e0 	ldr	x0, [sp, #168]
   2a428:	f94073e2 	ldr	x2, [sp, #224]
   2a42c:	52800001 	mov	w1, #0x0                   	// #0
   2a430:	d0ffffd3 	adrp	x19, 24000 <(anonymous namespace)::coarse_gcr_fused_step(std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, double&) [clone ._omp_fn.1]+0x1a0>
   2a434:	97ff6b1b 	bl	50a0 <memset@plt>
   2a438:	a95567f7 	ldp	x23, x25, [sp, #336]
   2a43c:	9120c260 	add	x0, x19, #0x830
   2a440:	52801913 	mov	w19, #0xc8                  	// #200
   2a444:	eb17033f 	cmp	x25, x23
   2a448:	54000920 	b.eq	2a56c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xb4c>  // b.none
   2a44c:	aa1c03f8 	mov	x24, x28
   2a450:	aa1b03fc 	mov	x28, x27
   2a454:	f94067fb 	ldr	x27, [sp, #200]
   2a458:	f90043fa 	str	x26, [sp, #128]
   2a45c:	aa1903fa 	mov	x26, x25
   2a460:	aa0003f9 	mov	x25, x0
   2a464:	d503201f 	nop
   2a468:	b94002f6 	ldr	w22, [x23]
   2a46c:	0b1606c0 	add	w0, w22, w22, lsl #1
   2a470:	9b3372d5 	smaddl	x21, w22, w19, x28
   2a474:	93407c02 	sxtw	x2, w0
   2a478:	8b20cf74 	add	x20, x27, w0, sxtw #3
   2a47c:	fc627b60 	ldr	d0, [x27, x2, lsl #3]
   2a480:	1e602008 	fcmp	d0, #0.0
   2a484:	540002a5 	b.pl	2a4d8 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xab8>  // b.nfrst
   2a488:	f9004be2 	str	x2, [sp, #144]
   2a48c:	97ff6cd5 	bl	57e0 <sqrt@plt>
   2a490:	1e6a2010 	fcmpe	d0, d10
   2a494:	540040e4 	b.mi	2acb0 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1290>  // b.first
   2a498:	f9404be2 	ldr	x2, [sp, #144]
   2a49c:	910122a0 	add	x0, x21, #0x48
   2a4a0:	9100c2a4 	add	x4, x21, #0x30
   2a4a4:	fc627b60 	ldr	d0, [x27, x2, lsl #3]
   2a4a8:	910182a2 	add	x2, x21, #0x60
   2a4ac:	910062b5 	add	x21, x21, #0x18
   2a4b0:	1e602008 	fcmp	d0, #0.0
   2a4b4:	5400ba65 	b.pl	2bc00 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x21e0>  // b.nfrst
   2a4b8:	f9004be0 	str	x0, [sp, #144]
   2a4bc:	f90053e4 	str	x4, [sp, #160]
   2a4c0:	f9009fe2 	str	x2, [sp, #312]
   2a4c4:	97ff6cc7 	bl	57e0 <sqrt@plt>
   2a4c8:	f9404be0 	ldr	x0, [sp, #144]
   2a4cc:	f94053e4 	ldr	x4, [sp, #160]
   2a4d0:	f9409fe2 	ldr	x2, [sp, #312]
   2a4d4:	14000008 	b	2a4f4 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xad4>
   2a4d8:	1e61c000 	fsqrt	d0, d0
   2a4dc:	1e6a2010 	fcmpe	d0, d10
   2a4e0:	54003e84 	b.mi	2acb0 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1290>  // b.first
   2a4e4:	910182a2 	add	x2, x21, #0x60
   2a4e8:	910122a0 	add	x0, x21, #0x48
   2a4ec:	9100c2a4 	add	x4, x21, #0x30
   2a4f0:	910062b5 	add	x21, x21, #0x18
   2a4f4:	6d408682 	ldp	d2, d1, [x20, #8]
   2a4f8:	fd00d3e0 	str	d0, [sp, #416]
   2a4fc:	52800003 	mov	w3, #0x0                   	// #0
   2a500:	aa1803e1 	mov	x1, x24
   2a504:	a91803e2 	stp	x2, x0, [sp, #384]
   2a508:	a91957e4 	stp	x4, x21, [sp, #400]
   2a50c:	aa1903e0 	mov	x0, x25
   2a510:	a9400844 	ldp	x4, x2, [x2]
   2a514:	f900d7ff 	str	xzr, [sp, #424]
   2a518:	1e601842 	fdiv	d2, d2, d0
   2a51c:	cb040042 	sub	x2, x2, x4
   2a520:	d2835004 	mov	x4, #0x1a80                	// #6784
   2a524:	1e601820 	fdiv	d0, d1, d0
   2a528:	f2a000c4 	movk	x4, #0x6, lsl #16
   2a52c:	eb04005f 	cmp	x2, x4
   2a530:	1a9f87e2 	cset	w2, ls  // ls = plast
   2a534:	1e624041 	fcvt	s1, d2
   2a538:	1e624000 	fcvt	s0, d0
   2a53c:	bd01b3e1 	str	s1, [sp, #432]
   2a540:	bd01b7e0 	str	s0, [sp, #436]
   2a544:	97ff6c03 	bl	5550 <GOMP_parallel@plt>
   2a548:	fd40d7e0 	ldr	d0, [sp, #424]
   2a54c:	f94057e0 	ldr	x0, [sp, #168]
   2a550:	fc36d800 	str	d0, [x0, w22, sxtw #3]
   2a554:	910012f7 	add	x23, x23, #0x4
   2a558:	eb1a02ff 	cmp	x23, x26
   2a55c:	54fff861 	b.ne	2a468 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xa48>  // b.any
   2a560:	f94043fa 	ldr	x26, [sp, #128]
   2a564:	aa1c03fb 	mov	x27, x28
   2a568:	aa1803fc 	mov	x28, x24
   2a56c:	b00002a0 	adrp	x0, 7f000 <__FRAME_END__+0x1ea64>
   2a570:	f9475800 	ldr	x0, [x0, #3760]
   2a574:	b9400000 	ldr	w0, [x0]
   2a578:	7100041f 	cmp	w0, #0x1
   2a57c:	54004c6c 	b.gt	2af08 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x14e8>
   2a580:	a95687e0 	ldp	x0, x1, [sp, #360]
   2a584:	eb01001f 	cmp	x0, x1
   2a588:	54000040 	b.eq	2a590 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xb70>  // b.none
   2a58c:	f900bbe0 	str	x0, [sp, #368]
   2a590:	a95557f4 	ldp	x20, x21, [sp, #336]
   2a594:	eb1402bf 	cmp	x21, x20
   2a598:	54004860 	b.eq	2aea4 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1484>  // b.none
   2a59c:	52801917 	mov	w23, #0xc8                  	// #200
   2a5a0:	910533f8 	add	x24, sp, #0x14c
   2a5a4:	1e7e1008 	fmov	d8, #-1.000000000000000000e+00
   2a5a8:	b9400280 	ldr	w0, [x20]
   2a5ac:	9b376c13 	smaddl	x19, w0, w23, x27
   2a5b0:	b9014fe0 	str	w0, [sp, #332]
   2a5b4:	39431261 	ldrb	w1, [x19, #196]
   2a5b8:	350005a1 	cbnz	w1, 2a66c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xc4c>
   2a5bc:	f94057e1 	ldr	x1, [sp, #168]
   2a5c0:	fc60d820 	ldr	d0, [x1, w0, sxtw #3]
   2a5c4:	1e602008 	fcmp	d0, #0.0
   2a5c8:	54000065 	b.pl	2a5d4 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xbb4>  // b.nfrst
   2a5cc:	97ff6c85 	bl	57e0 <sqrt@plt>
   2a5d0:	14000002 	b	2a5d8 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xbb8>
   2a5d4:	1e61c000 	fsqrt	d0, d0
   2a5d8:	9101e260 	add	x0, x19, #0x78
   2a5dc:	a9408801 	ldp	x1, x2, [x0, #8]
   2a5e0:	fd005a60 	str	d0, [x19, #176]
   2a5e4:	eb02003f 	cmp	x1, x2
   2a5e8:	54004580 	b.eq	2ae98 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1478>  // b.none
   2a5ec:	aa1303e2 	mov	x2, x19
   2a5f0:	91006023 	add	x3, x1, #0x18
   2a5f4:	3cc48c40 	ldr	q0, [x2, #72]!
   2a5f8:	f9400844 	ldr	x4, [x2, #16]
   2a5fc:	f900085f 	str	xzr, [x2, #16]
   2a600:	3d800020 	str	q0, [x1]
   2a604:	a904fe7f 	stp	xzr, xzr, [x19, #72]
   2a608:	f9000824 	str	x4, [x1, #16]
   2a60c:	f9000403 	str	x3, [x0, #8]
   2a610:	91024260 	add	x0, x19, #0x90
   2a614:	a9408801 	ldp	x1, x2, [x0, #8]
   2a618:	eb02003f 	cmp	x1, x2
   2a61c:	54004360 	b.eq	2ae88 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1468>  // b.none
   2a620:	aa1303e3 	mov	x3, x19
   2a624:	91006022 	add	x2, x1, #0x18
   2a628:	3cc60c60 	ldr	q0, [x3, #96]!
   2a62c:	f9400864 	ldr	x4, [x3, #16]
   2a630:	f900087f 	str	xzr, [x3, #16]
   2a634:	3d800020 	str	q0, [x1]
   2a638:	a9067e7f 	stp	xzr, xzr, [x19, #96]
   2a63c:	f9000824 	str	x4, [x1, #16]
   2a640:	f9000402 	str	x2, [x0, #8]
   2a644:	f94047e0 	ldr	x0, [sp, #136]
   2a648:	6d4a8662 	ldp	d2, d1, [x19, #168]
   2a64c:	fd44e400 	ldr	d0, [x0, #2504]
   2a650:	f9404a60 	ldr	x0, [x19, #144]
   2a654:	cb000042 	sub	x2, x2, x0
   2a658:	1e620800 	fmul	d0, d0, d2
   2a65c:	1e602030 	fcmpe	d1, d0
   2a660:	54003c84 	b.mi	2adf0 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x13d0>  // b.first
   2a664:	f106005f 	cmp	x2, #0x180
   2a668:	54003c40 	b.eq	2adf0 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x13d0>  // b.none
   2a66c:	91001294 	add	x20, x20, #0x4
   2a670:	eb1402bf 	cmp	x21, x20
   2a674:	54fff9a1 	b.ne	2a5a8 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xb88>  // b.any
   2a678:	a956cff6 	ldp	x22, x19, [sp, #360]
   2a67c:	eb16027f 	cmp	x19, x22
   2a680:	54004120 	b.eq	2aea4 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1484>  // b.none
   2a684:	f94057f8 	ldr	x24, [sp, #168]
   2a688:	f94073e2 	ldr	x2, [sp, #224]
   2a68c:	d0ffffc3 	adrp	x3, 24000 <(anonymous namespace)::coarse_gcr_fused_step(std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, double&) [clone ._omp_fn.1]+0x1a0>
   2a690:	52800001 	mov	w1, #0x0                   	// #0
   2a694:	2f00e408 	movi	d8, #0x0
   2a698:	52801915 	mov	w21, #0xc8                  	// #200
   2a69c:	91280074 	add	x20, x3, #0xa00
   2a6a0:	aa1803e0 	mov	x0, x24
   2a6a4:	97ff6a7f 	bl	50a0 <memset@plt>
   2a6a8:	b84046d7 	ldr	w23, [x22], #4
   2a6ac:	52800003 	mov	w3, #0x0                   	// #0
   2a6b0:	aa1c03e1 	mov	x1, x28
   2a6b4:	aa1403e0 	mov	x0, x20
   2a6b8:	fd00c7e8 	str	d8, [sp, #392]
   2a6bc:	9b356ee2 	smaddl	x2, w23, w21, x27
   2a6c0:	91006044 	add	x4, x2, #0x18
   2a6c4:	a9418845 	ldp	x5, x2, [x2, #24]
   2a6c8:	f900c3e4 	str	x4, [sp, #384]
   2a6cc:	d2835004 	mov	x4, #0x1a80                	// #6784
   2a6d0:	f2a000c4 	movk	x4, #0x6, lsl #16
   2a6d4:	cb050042 	sub	x2, x2, x5
   2a6d8:	eb04005f 	cmp	x2, x4
   2a6dc:	1a9f87e2 	cset	w2, ls  // ls = plast
   2a6e0:	97ff6b9c 	bl	5550 <GOMP_parallel@plt>
   2a6e4:	fd40c7e0 	ldr	d0, [sp, #392]
   2a6e8:	fc37db00 	str	d0, [x24, w23, sxtw #3]
   2a6ec:	eb1302df 	cmp	x22, x19
   2a6f0:	54fffdc1 	b.ne	2a6a8 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xc88>  // b.any
   2a6f4:	b00002a0 	adrp	x0, 7f000 <__FRAME_END__+0x1ea64>
   2a6f8:	f9475800 	ldr	x0, [x0, #3760]
   2a6fc:	b9400000 	ldr	w0, [x0]
   2a700:	7100041f 	cmp	w0, #0x1
   2a704:	5400422c 	b.gt	2af48 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1528>
   2a708:	b940dbe0 	ldr	w0, [sp, #216]
   2a70c:	a956dff4 	ldp	x20, x23, [sp, #360]
   2a710:	11000c00 	add	w0, w0, #0x3
   2a714:	b900dbe0 	str	w0, [sp, #216]
   2a718:	eb1402ff 	cmp	x23, x20
   2a71c:	54000580 	b.eq	2a7cc <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xdac>  // b.none
   2a720:	f94057f6 	ldr	x22, [sp, #168]
   2a724:	f90043fa 	str	x26, [sp, #128]
   2a728:	b9400295 	ldr	w21, [x20]
   2a72c:	52801900 	mov	w0, #0xc8                  	// #200
   2a730:	fc75dac0 	ldr	d0, [x22, w21, sxtw #3]
   2a734:	9b206eb5 	smaddl	x21, w21, w0, x27
   2a738:	1e602008 	fcmp	d0, #0.0
   2a73c:	54000065 	b.pl	2a748 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xd28>  // b.nfrst
   2a740:	97ff6c28 	bl	57e0 <sqrt@plt>
   2a744:	14000002 	b	2a74c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xd2c>
   2a748:	1e61c000 	fsqrt	d0, d0
   2a74c:	f9404ab8 	ldr	x24, [x21, #144]
   2a750:	f9404eba 	ldr	x26, [x21, #152]
   2a754:	910242b9 	add	x25, x21, #0x90
   2a758:	fd005aa0 	str	d0, [x21, #176]
   2a75c:	eb1a031f 	cmp	x24, x26
   2a760:	54000120 	b.eq	2a784 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xd64>  // b.none
   2a764:	aa1803f3 	mov	x19, x24
   2a768:	f9400260 	ldr	x0, [x19]
   2a76c:	91006273 	add	x19, x19, #0x18
   2a770:	b40029a0 	cbz	x0, 2aca4 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1284>
   2a774:	97ff6a43 	bl	5080 <free@plt>
   2a778:	eb13035f 	cmp	x26, x19
   2a77c:	54ffff61 	b.ne	2a768 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xd48>  // b.any
   2a780:	f9000738 	str	x24, [x25, #8]
   2a784:	9101e2b8 	add	x24, x21, #0x78
   2a788:	f9400719 	ldr	x25, [x24, #8]
   2a78c:	f9403eb5 	ldr	x21, [x21, #120]
   2a790:	eb1902bf 	cmp	x21, x25
   2a794:	54000140 	b.eq	2a7bc <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xd9c>  // b.none
   2a798:	aa1503f3 	mov	x19, x21
   2a79c:	d503201f 	nop
   2a7a0:	f9400260 	ldr	x0, [x19]
   2a7a4:	91006273 	add	x19, x19, #0x18
   2a7a8:	b4002780 	cbz	x0, 2ac98 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1278>
   2a7ac:	97ff6a35 	bl	5080 <free@plt>
   2a7b0:	eb13033f 	cmp	x25, x19
   2a7b4:	54ffff61 	b.ne	2a7a0 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xd80>  // b.any
   2a7b8:	f9000715 	str	x21, [x24, #8]
   2a7bc:	91001294 	add	x20, x20, #0x4
   2a7c0:	eb17029f 	cmp	x20, x23
   2a7c4:	54fffb21 	b.ne	2a728 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xd08>  // b.any
   2a7c8:	f94043fa 	ldr	x26, [sp, #128]
   2a7cc:	f94047e0 	ldr	x0, [sp, #136]
   2a7d0:	b940dfe1 	ldr	w1, [sp, #220]
   2a7d4:	b94ad800 	ldr	w0, [x0, #2776]
   2a7d8:	11000421 	add	w1, w1, #0x1
   2a7dc:	b900dfe1 	str	w1, [sp, #220]
   2a7e0:	6b01001f 	cmp	w0, w1
   2a7e4:	54ffcaac 	b.gt	2a138 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x718>
   2a7e8:	fd405760 	ldr	d0, [x27, #168]
   2a7ec:	1e602008 	fcmp	d0, #0.0
   2a7f0:	54004301 	b.ne	2b050 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1630>  // b.any
   2a7f4:	f9409be0 	ldr	x0, [sp, #304]
   2a7f8:	fd405400 	ldr	d0, [x0, #168]
   2a7fc:	1e602008 	fcmp	d0, #0.0
   2a800:	54004141 	b.ne	2b028 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1608>  // b.any
   2a804:	b9409fe0 	ldr	w0, [sp, #156]
   2a808:	7100081f 	cmp	w0, #0x2
   2a80c:	54000880 	b.eq	2a91c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xefc>  // b.none
   2a810:	fd411f60 	ldr	d0, [x27, #568]
   2a814:	1e602008 	fcmp	d0, #0.0
   2a818:	54004ac1 	b.ne	2b170 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1750>  // b.any
   2a81c:	b9409fe0 	ldr	w0, [sp, #156]
   2a820:	71000c1f 	cmp	w0, #0x3
   2a824:	540007c0 	b.eq	2a91c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xefc>  // b.none
   2a828:	fd418360 	ldr	d0, [x27, #768]
   2a82c:	1e602008 	fcmp	d0, #0.0
   2a830:	540071a1 	b.ne	2b664 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1c44>  // b.any
   2a834:	b9409fe0 	ldr	w0, [sp, #156]
   2a838:	7100101f 	cmp	w0, #0x4
   2a83c:	54000700 	b.eq	2a91c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xefc>  // b.none
   2a840:	fd41e760 	ldr	d0, [x27, #968]
   2a844:	1e602008 	fcmp	d0, #0.0
   2a848:	54007221 	b.ne	2b68c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1c6c>  // b.any
   2a84c:	b9409fe0 	ldr	w0, [sp, #156]
   2a850:	7100141f 	cmp	w0, #0x5
   2a854:	54000640 	b.eq	2a91c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xefc>  // b.none
   2a858:	fd424b60 	ldr	d0, [x27, #1168]
   2a85c:	1e602008 	fcmp	d0, #0.0
   2a860:	540072a1 	b.ne	2b6b4 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1c94>  // b.any
   2a864:	b9409fe0 	ldr	w0, [sp, #156]
   2a868:	7100181f 	cmp	w0, #0x6
   2a86c:	54000580 	b.eq	2a91c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xefc>  // b.none
   2a870:	fd42af60 	ldr	d0, [x27, #1368]
   2a874:	1e602008 	fcmp	d0, #0.0
   2a878:	54008c61 	b.ne	2ba04 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1fe4>  // b.any
   2a87c:	b9409fe0 	ldr	w0, [sp, #156]
   2a880:	71001c1f 	cmp	w0, #0x7
   2a884:	540004c0 	b.eq	2a91c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xefc>  // b.none
   2a888:	fd431360 	ldr	d0, [x27, #1568]
   2a88c:	1e602008 	fcmp	d0, #0.0
   2a890:	54008341 	b.ne	2b8f8 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1ed8>  // b.any
   2a894:	b9409fe0 	ldr	w0, [sp, #156]
   2a898:	7100201f 	cmp	w0, #0x8
   2a89c:	54000400 	b.eq	2a91c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xefc>  // b.none
   2a8a0:	fd437760 	ldr	d0, [x27, #1768]
   2a8a4:	1e602008 	fcmp	d0, #0.0
   2a8a8:	54008141 	b.ne	2b8d0 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1eb0>  // b.any
   2a8ac:	b9409fe0 	ldr	w0, [sp, #156]
   2a8b0:	7100241f 	cmp	w0, #0x9
   2a8b4:	54000340 	b.eq	2a91c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xefc>  // b.none
   2a8b8:	fd43db60 	ldr	d0, [x27, #1968]
   2a8bc:	1e602008 	fcmp	d0, #0.0
   2a8c0:	54007f41 	b.ne	2b8a8 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1e88>  // b.any
   2a8c4:	b9409fe0 	ldr	w0, [sp, #156]
   2a8c8:	7100281f 	cmp	w0, #0xa
   2a8cc:	54000280 	b.eq	2a91c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xefc>  // b.none
   2a8d0:	fd443f60 	ldr	d0, [x27, #2168]
   2a8d4:	91200362 	add	x2, x27, #0x800
   2a8d8:	1e602008 	fcmp	d0, #0.0
   2a8dc:	540097c1 	b.ne	2bbd4 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x21b4>  // b.any
   2a8e0:	b9409fe0 	ldr	w0, [sp, #156]
   2a8e4:	71002c1f 	cmp	w0, #0xb
   2a8e8:	540001a0 	b.eq	2a91c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xefc>  // b.none
   2a8ec:	fd44a360 	ldr	d0, [x27, #2368]
   2a8f0:	1e602008 	fcmp	d0, #0.0
   2a8f4:	54000140 	b.eq	2a91c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xefc>  // b.none
   2a8f8:	f94063e0 	ldr	x0, [sp, #192]
   2a8fc:	91232362 	add	x2, x27, #0x8c8
   2a900:	f9400003 	ldr	x3, [x0]
   2a904:	f9405be0 	ldr	x0, [sp, #176]
   2a908:	f9400001 	ldr	x1, [x0]
   2a90c:	f94047e0 	ldr	x0, [sp, #136]
   2a910:	91042063 	add	x3, x3, #0x108
   2a914:	91042021 	add	x1, x1, #0x108
   2a918:	97fff65a 	bl	28280 <NativeMG::Impl::coarse_reconstruct(std::vector<float, lqcd_native::WorkspaceAllocator<float> > const&, std::vector<float, lqcd_native::WorkspaceAllocator<float> > const&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&) const>
   2a91c:	d0000160 	adrp	x0, 58000 <typeinfo name for lqcd::Error+0x88>
   2a920:	52800001 	mov	w1, #0x0                   	// #0
   2a924:	91262000 	add	x0, x0, #0x988
   2a928:	97ff8a9e 	bl	d3a0 <lqcd_native::detail::setting(char const*, int)>
   2a92c:	34001160 	cbz	w0, 2ab58 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1138>
   2a930:	b00002a0 	adrp	x0, 7f000 <__FRAME_END__+0x1ea64>
   2a934:	f947c800 	ldr	x0, [x0, #3984]
   2a938:	b9400000 	ldr	w0, [x0]
   2a93c:	350010e0 	cbnz	w0, 2ab58 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1138>
   2a940:	b00002b3 	adrp	x19, 7f000 <__FRAME_END__+0x1ea64>
   2a944:	d0000161 	adrp	x1, 58000 <typeinfo name for lqcd::Error+0x88>
   2a948:	d2800462 	mov	x2, #0x23                  	// #35
   2a94c:	f947de60 	ldr	x0, [x19, #4024]
   2a950:	91266021 	add	x1, x1, #0x998
   2a954:	97ff6a67 	bl	52f0 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2a958:	f947de60 	ldr	x0, [x19, #4024]
   2a95c:	b9409fe1 	ldr	w1, [sp, #156]
   2a960:	97ff6b5c 	bl	56d0 <std::ostream::operator<<(int)@plt>
   2a964:	d0000161 	adrp	x1, 58000 <typeinfo name for lqcd::Error+0x88>
   2a968:	d2800262 	mov	x2, #0x13                  	// #19
   2a96c:	aa0003f4 	mov	x20, x0
   2a970:	91270021 	add	x1, x1, #0x9c0
   2a974:	97ff6a5f 	bl	52f0 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2a978:	f94047f5 	ldr	x21, [sp, #136]
   2a97c:	aa1403e0 	mov	x0, x20
   2a980:	b94adaa1 	ldr	w1, [x21, #2776]
   2a984:	97ff6b53 	bl	56d0 <std::ostream::operator<<(int)@plt>
   2a988:	d0000161 	adrp	x1, 58000 <typeinfo name for lqcd::Error+0x88>
   2a98c:	d2800282 	mov	x2, #0x14                  	// #20
   2a990:	aa0003f4 	mov	x20, x0
   2a994:	91276021 	add	x1, x1, #0x9d8
   2a998:	97ff6a56 	bl	52f0 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2a99c:	fd44e6a0 	ldr	d0, [x21, #2504]
   2a9a0:	aa1403e0 	mov	x0, x20
   2a9a4:	97ff6b17 	bl	5600 <std::ostream& std::ostream::_M_insert<double>(double)@plt>
   2a9a8:	d0000161 	adrp	x1, 58000 <typeinfo name for lqcd::Error+0x88>
   2a9ac:	d2800282 	mov	x2, #0x14                  	// #20
   2a9b0:	aa0003f4 	mov	x20, x0
   2a9b4:	9127c021 	add	x1, x1, #0x9f0
   2a9b8:	97ff6a4e 	bl	52f0 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2a9bc:	b940dbf5 	ldr	w21, [sp, #216]
   2a9c0:	aa1403e0 	mov	x0, x20
   2a9c4:	2a1503e1 	mov	w1, w21
   2a9c8:	97ff6b42 	bl	56d0 <std::ostream::operator<<(int)@plt>
   2a9cc:	d0000161 	adrp	x1, 58000 <typeinfo name for lqcd::Error+0x88>
   2a9d0:	d2800262 	mov	x2, #0x13                  	// #19
   2a9d4:	aa0003f4 	mov	x20, x0
   2a9d8:	91282021 	add	x1, x1, #0xa08
   2a9dc:	97ff6a45 	bl	52f0 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2a9e0:	b00002a0 	adrp	x0, 7f000 <__FRAME_END__+0x1ea64>
   2a9e4:	f9475801 	ldr	x1, [x0, #3760]
   2a9e8:	aa1403e0 	mov	x0, x20
   2a9ec:	b9400021 	ldr	w1, [x1]
   2a9f0:	7100043f 	cmp	w1, #0x1
   2a9f4:	1a9fc2a1 	csel	w1, w21, wzr, gt
   2a9f8:	97ff6b36 	bl	56d0 <std::ostream::operator<<(int)@plt>
   2a9fc:	d00002a0 	adrp	x0, 80000 <std::ostream::put(char)@GLIBCXX_3.4>
   2aa00:	d0000161 	adrp	x1, 58000 <typeinfo name for lqcd::Error+0x88>
   2aa04:	d0000177 	adrp	x23, 58000 <typeinfo name for lqcd::Error+0x88>
   2aa08:	9117c000 	add	x0, x0, #0x5f0
   2aa0c:	9128a021 	add	x1, x1, #0xa28
   2aa10:	aa1c03f8 	mov	x24, x28
   2aa14:	4c40a000 	ld1	{v0.16b, v1.16b}, [x0]
   2aa18:	912522f7 	add	x23, x23, #0x948
   2aa1c:	52800016 	mov	w22, #0x0                   	// #0
   2aa20:	d0000179 	adrp	x25, 58000 <typeinfo name for lqcd::Error+0x88>
   2aa24:	f9004be1 	str	x1, [sp, #144]
   2aa28:	4c00a380 	st1	{v0.16b, v1.16b}, [x28]
   2aa2c:	f947de60 	ldr	x0, [x19, #4024]
   2aa30:	d2800042 	mov	x2, #0x2                   	// #2
   2aa34:	91288321 	add	x1, x25, #0xa20
   2aa38:	97ff6a2e 	bl	52f0 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2aa3c:	f9400314 	ldr	x20, [x24]
   2aa40:	b40040b4 	cbz	x20, 2b254 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1834>
   2aa44:	aa1403e0 	mov	x0, x20
   2aa48:	97ff694a 	bl	4f70 <strlen@plt>
   2aa4c:	aa0003e2 	mov	x2, x0
   2aa50:	f947de60 	ldr	x0, [x19, #4024]
   2aa54:	aa1403e1 	mov	x1, x20
   2aa58:	97ff6a26 	bl	52f0 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2aa5c:	f947de60 	ldr	x0, [x19, #4024]
   2aa60:	f9404be1 	ldr	x1, [sp, #144]
   2aa64:	d2800062 	mov	x2, #0x3                   	// #3
   2aa68:	97ff6a22 	bl	52f0 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2aa6c:	34003a76 	cbz	w22, 2b1b8 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1798>
   2aa70:	710006df 	cmp	w22, #0x1
   2aa74:	54006980 	b.eq	2b7a4 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1d84>  // b.none
   2aa78:	71000adf 	cmp	w22, #0x2
   2aa7c:	54006c20 	b.eq	2b800 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1de0>  // b.none
   2aa80:	d000017c 	adrp	x28, 58000 <typeinfo name for lqcd::Error+0x88>
   2aa84:	9102a375 	add	x21, x27, #0xa8
   2aa88:	52800014 	mov	w20, #0x0                   	// #0
   2aa8c:	9132c380 	add	x0, x28, #0xcb0
   2aa90:	f90043e0 	str	x0, [sp, #128]
   2aa94:	394072a0 	ldrb	w0, [x21, #28]
   2aa98:	35003800 	cbnz	w0, 2b198 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1778>
   2aa9c:	f94047e1 	ldr	x1, [sp, #136]
   2aaa0:	b94012a0 	ldr	w0, [x21, #16]
   2aaa4:	5280001c 	mov	w28, #0x0                   	// #0
   2aaa8:	b94ad821 	ldr	w1, [x1, #2776]
   2aaac:	6b00003f 	cmp	w1, w0
   2aab0:	540034c0 	b.eq	2b148 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1728>  // b.none
   2aab4:	34003594 	cbz	w20, 2b164 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1744>
   2aab8:	d2800022 	mov	x2, #0x1                   	// #1
   2aabc:	aa1703e1 	mov	x1, x23
   2aac0:	f947de60 	ldr	x0, [x19, #4024]
   2aac4:	97ff6a0b 	bl	52f0 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2aac8:	f947de60 	ldr	x0, [x19, #4024]
   2aacc:	2a1c03e1 	mov	w1, w28
   2aad0:	97ff6b00 	bl	56d0 <std::ostream::operator<<(int)@plt>
   2aad4:	b9409fe0 	ldr	w0, [sp, #156]
   2aad8:	11000694 	add	w20, w20, #0x1
   2aadc:	910322b5 	add	x21, x21, #0xc8
   2aae0:	6b14001f 	cmp	w0, w20
   2aae4:	54fffd8c 	b.gt	2aa94 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1074>
   2aae8:	f947de60 	ldr	x0, [x19, #4024]
   2aaec:	52800ba3 	mov	w3, #0x5d                  	// #93
   2aaf0:	d2800022 	mov	x2, #0x1                   	// #1
   2aaf4:	910533e1 	add	x1, sp, #0x14c
   2aaf8:	390533e3 	strb	w3, [sp, #332]
   2aafc:	97ff69fd 	bl	52f0 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2ab00:	110006d6 	add	w22, w22, #0x1
   2ab04:	91002318 	add	x24, x24, #0x8
   2ab08:	710012df 	cmp	w22, #0x4
   2ab0c:	54fff901 	b.ne	2aa2c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x100c>  // b.any
   2ab10:	f947de60 	ldr	x0, [x19, #4024]
   2ab14:	52800fa3 	mov	w3, #0x7d                  	// #125
   2ab18:	d2800022 	mov	x2, #0x1                   	// #1
   2ab1c:	91052fe1 	add	x1, sp, #0x14b
   2ab20:	39052fe3 	strb	w3, [sp, #331]
   2ab24:	97ff69f3 	bl	52f0 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2ab28:	aa0003f4 	mov	x20, x0
   2ab2c:	f9400000 	ldr	x0, [x0]
   2ab30:	f85e8000 	ldur	x0, [x0, #-24]
   2ab34:	8b000280 	add	x0, x20, x0
   2ab38:	f9407813 	ldr	x19, [x0, #240]
   2ab3c:	b4008613 	cbz	x19, 2bbfc <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x21dc>
   2ab40:	3940e260 	ldrb	w0, [x19, #56]
   2ab44:	34006160 	cbz	w0, 2b770 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1d50>
   2ab48:	39410e61 	ldrb	w1, [x19, #67]
   2ab4c:	aa1403e0 	mov	x0, x20
   2ab50:	97ff68c8 	bl	4e70 <std::ostream::put(char)@plt>
   2ab54:	97ff697f 	bl	5150 <std::ostream::flush()@plt>
   2ab58:	f94067e0 	ldr	x0, [sp, #200]
   2ab5c:	f9407be1 	ldr	x1, [sp, #240]
   2ab60:	97ff69bc 	bl	5250 <operator delete(void*, unsigned long)@plt>
   2ab64:	f9405fe1 	ldr	x1, [sp, #184]
   2ab68:	aa1a03e0 	mov	x0, x26
   2ab6c:	97ff69b9 	bl	5250 <operator delete(void*, unsigned long)@plt>
   2ab70:	f940b7e0 	ldr	x0, [sp, #360]
   2ab74:	b4000080 	cbz	x0, 2ab84 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1164>
   2ab78:	f940bfe1 	ldr	x1, [sp, #376]
   2ab7c:	cb000021 	sub	x1, x1, x0
   2ab80:	97ff69b4 	bl	5250 <operator delete(void*, unsigned long)@plt>
   2ab84:	f940abe0 	ldr	x0, [sp, #336]
   2ab88:	b4000080 	cbz	x0, 2ab98 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1178>
   2ab8c:	f940b3e1 	ldr	x1, [sp, #352]
   2ab90:	cb000021 	sub	x1, x1, x0
   2ab94:	97ff69af 	bl	5250 <operator delete(void*, unsigned long)@plt>
   2ab98:	f94057e0 	ldr	x0, [sp, #168]
   2ab9c:	f94073e1 	ldr	x1, [sp, #224]
   2aba0:	aa1b03f4 	mov	x20, x27
   2aba4:	97ff69ab 	bl	5250 <operator delete(void*, unsigned long)@plt>
   2aba8:	a9495693 	ldp	x19, x21, [x20, #144]
   2abac:	eb15027f 	cmp	x19, x21
   2abb0:	54000120 	b.eq	2abd4 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x11b4>  // b.none
   2abb4:	d503201f 	nop
   2abb8:	f9400260 	ldr	x0, [x19]
   2abbc:	91006273 	add	x19, x19, #0x18
   2abc0:	b4000860 	cbz	x0, 2accc <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x12ac>
   2abc4:	97ff692f 	bl	5080 <free@plt>
   2abc8:	eb1302bf 	cmp	x21, x19
   2abcc:	54ffff61 	b.ne	2abb8 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1198>  // b.any
   2abd0:	f9404a95 	ldr	x21, [x20, #144]
   2abd4:	b40000b5 	cbz	x21, 2abe8 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x11c8>
   2abd8:	f9405281 	ldr	x1, [x20, #160]
   2abdc:	aa1503e0 	mov	x0, x21
   2abe0:	cb150021 	sub	x1, x1, x21
   2abe4:	97ff699b 	bl	5250 <operator delete(void*, unsigned long)@plt>
   2abe8:	a947d693 	ldp	x19, x21, [x20, #120]
   2abec:	eb15027f 	cmp	x19, x21
   2abf0:	54000120 	b.eq	2ac14 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x11f4>  // b.none
   2abf4:	d503201f 	nop
   2abf8:	f9400260 	ldr	x0, [x19]
   2abfc:	91006273 	add	x19, x19, #0x18
   2ac00:	b40005e0 	cbz	x0, 2acbc <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x129c>
   2ac04:	97ff691f 	bl	5080 <free@plt>
   2ac08:	eb1302bf 	cmp	x21, x19
   2ac0c:	54ffff61 	b.ne	2abf8 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x11d8>  // b.any
   2ac10:	f9403e95 	ldr	x21, [x20, #120]
   2ac14:	b40000b5 	cbz	x21, 2ac28 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1208>
   2ac18:	f9404681 	ldr	x1, [x20, #136]
   2ac1c:	aa1503e0 	mov	x0, x21
   2ac20:	cb150021 	sub	x1, x1, x21
   2ac24:	97ff698b 	bl	5250 <operator delete(void*, unsigned long)@plt>
   2ac28:	f9403280 	ldr	x0, [x20, #96]
   2ac2c:	b4000040 	cbz	x0, 2ac34 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1214>
   2ac30:	97ff6914 	bl	5080 <free@plt>
   2ac34:	f9402680 	ldr	x0, [x20, #72]
   2ac38:	b4000040 	cbz	x0, 2ac40 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1220>
   2ac3c:	97ff6911 	bl	5080 <free@plt>
   2ac40:	f9401a80 	ldr	x0, [x20, #48]
   2ac44:	b4000040 	cbz	x0, 2ac4c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x122c>
   2ac48:	97ff690e 	bl	5080 <free@plt>
   2ac4c:	f9400e80 	ldr	x0, [x20, #24]
   2ac50:	b4000040 	cbz	x0, 2ac58 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1238>
   2ac54:	97ff690b 	bl	5080 <free@plt>
   2ac58:	f9400280 	ldr	x0, [x20]
   2ac5c:	91032294 	add	x20, x20, #0xc8
   2ac60:	b4001340 	cbz	x0, 2aec8 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x14a8>
   2ac64:	97ff6907 	bl	5080 <free@plt>
   2ac68:	f94077e0 	ldr	x0, [sp, #232]
   2ac6c:	eb14001f 	cmp	x0, x20
   2ac70:	54fff9c1 	b.ne	2aba8 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1188>  // b.any
   2ac74:	f94083e1 	ldr	x1, [sp, #256]
   2ac78:	aa1b03e0 	mov	x0, x27
   2ac7c:	97ff6975 	bl	5250 <operator delete(void*, unsigned long)@plt>
   2ac80:	b94123e0 	ldr	w0, [sp, #288]
   2ac84:	35002cc0 	cbnz	w0, 2b21c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x17fc>
   2ac88:	a9446bf9 	ldp	x25, x26, [sp, #64]
   2ac8c:	a94573fb 	ldp	x27, x28, [sp, #80]
   2ac90:	6d4627e8 	ldp	d8, d9, [sp, #96]
   2ac94:	17fffb9e 	b	29b0c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xec>
   2ac98:	eb13033f 	cmp	x25, x19
   2ac9c:	54ffd821 	b.ne	2a7a0 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xd80>  // b.any
   2aca0:	17fffec6 	b	2a7b8 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xd98>
   2aca4:	eb13035f 	cmp	x26, x19
   2aca8:	54ffd601 	b.ne	2a768 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xd48>  // b.any
   2acac:	17fffeb5 	b	2a780 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xd60>
   2acb0:	52800020 	mov	w0, #0x1                   	// #1
   2acb4:	390312a0 	strb	w0, [x21, #196]
   2acb8:	17fffe27 	b	2a554 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xb34>
   2acbc:	eb1302bf 	cmp	x21, x19
   2acc0:	54fff9c1 	b.ne	2abf8 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x11d8>  // b.any
   2acc4:	f9403e95 	ldr	x21, [x20, #120]
   2acc8:	17ffffd3 	b	2ac14 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x11f4>
   2accc:	eb1302bf 	cmp	x21, x19
   2acd0:	54fff741 	b.ne	2abb8 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1198>  // b.any
   2acd4:	f9404a95 	ldr	x21, [x20, #144]
   2acd8:	17ffffbf 	b	2abd4 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x11b4>
   2acdc:	b00002a5 	adrp	x5, 7f000 <__FRAME_END__+0x1ea64>
   2ace0:	b00002a4 	adrp	x4, 7f000 <__FRAME_END__+0x1ea64>
   2ace4:	b00002a3 	adrp	x3, 7f000 <__FRAME_END__+0x1ea64>
   2ace8:	b940d3e2 	ldr	w2, [sp, #208]
   2acec:	f94760a5 	ldr	x5, [x5, #3776]
   2acf0:	f9474884 	ldr	x4, [x4, #3728]
   2acf4:	aa1a03e1 	mov	x1, x26
   2acf8:	d2800020 	mov	x0, #0x1                   	// #1
   2acfc:	f9478063 	ldr	x3, [x3, #3840]
   2ad00:	f94000a5 	ldr	x5, [x5]
   2ad04:	97ff6997 	bl	5360 <MPI_Allreduce@plt>
   2ad08:	b94093e0 	ldr	w0, [sp, #144]
   2ad0c:	a9555ff3 	ldp	x19, x23, [sp, #336]
   2ad10:	b900dbe0 	str	w0, [sp, #216]
   2ad14:	eb1302ff 	cmp	x23, x19
   2ad18:	54ffad81 	b.ne	2a2c8 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x8a8>  // b.any
   2ad1c:	aa1303f4 	mov	x20, x19
   2ad20:	17fffd8b 	b	2a34c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x92c>
   2ad24:	f940b3e1 	ldr	x1, [sp, #352]
   2ad28:	eb01027f 	cmp	x19, x1
   2ad2c:	54000c40 	b.eq	2aeb4 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1494>  // b.none
   2ad30:	b8004660 	str	w0, [x19], #4
   2ad34:	f900aff3 	str	x19, [sp, #344]
   2ad38:	f94047e2 	ldr	x2, [sp, #136]
   2ad3c:	b940ba80 	ldr	w0, [x20, #184]
   2ad40:	91006296 	add	x22, x20, #0x18
   2ad44:	91012293 	add	x19, x20, #0x48
   2ad48:	395ec441 	ldrb	w1, [x2, #1969]
   2ad4c:	11000400 	add	w0, w0, #0x1
   2ad50:	b900ba80 	str	w0, [x20, #184]
   2ad54:	340000a1 	cbz	w1, 2ad68 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1348>
   2ad58:	395ecc40 	ldrb	w0, [x2, #1971]
   2ad5c:	35000060 	cbnz	w0, 2ad68 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1348>
   2ad60:	aa0203e0 	mov	x0, x2
   2ad64:	97fff24b 	bl	27690 <NativeMG::Impl::prepare_coarse_columns() const [clone .part.1]>
   2ad68:	f94006c1 	ldr	x1, [x22, #8]
   2ad6c:	f9400e83 	ldr	x3, [x20, #24]
   2ad70:	aa1c03e2 	mov	x2, x28
   2ad74:	aa1303e0 	mov	x0, x19
   2ad78:	b90183ff 	str	wzr, [sp, #384]
   2ad7c:	cb030021 	sub	x1, x1, x3
   2ad80:	9342fc21 	asr	x1, x1, #2
   2ad84:	94000463 	bl	2bf10 <std::vector<float, lqcd_native::WorkspaceAllocator<float> >::_M_fill_assign(unsigned long, float const&)>
   2ad88:	a9184ff6 	stp	x22, x19, [sp, #384]
   2ad8c:	f94047f6 	ldr	x22, [sp, #136]
   2ad90:	52800024 	mov	w4, #0x1                   	// #1
   2ad94:	52800002 	mov	w2, #0x0                   	// #0
   2ad98:	aa1c03e1 	mov	x1, x28
   2ad9c:	aa1703e0 	mov	x0, x23
   2ada0:	52800003 	mov	w3, #0x0                   	// #0
   2ada4:	b9019bff 	str	wzr, [sp, #408]
   2ada8:	390673e4 	strb	w4, [sp, #412]
   2adac:	f900cbf6 	str	x22, [sp, #400]
   2adb0:	97ff69e8 	bl	5550 <GOMP_parallel@plt>
   2adb4:	aa1303e1 	mov	x1, x19
   2adb8:	91018282 	add	x2, x20, #0x60
   2adbc:	aa1603e0 	mov	x0, x22
   2adc0:	97fff5a8 	bl	28460 <NativeMG::Impl::coarse_schur(std::vector<float, lqcd_native::WorkspaceAllocator<float> > const&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&) const>
   2adc4:	a9490682 	ldp	x2, x1, [x20, #144]
   2adc8:	b9414fe0 	ldr	w0, [sp, #332]
   2adcc:	f940aff3 	ldr	x19, [sp, #344]
   2add0:	cb020021 	sub	x1, x1, x2
   2add4:	f94053e2 	ldr	x2, [sp, #160]
   2add8:	9343fc21 	asr	x1, x1, #3
   2addc:	9b187c21 	mul	x1, x1, x24
   2ade0:	eb01005f 	cmp	x2, x1
   2ade4:	9a812041 	csel	x1, x2, x1, cs  // cs = hs, nlast
   2ade8:	f90053e1 	str	x1, [sp, #160]
   2adec:	17fffcea 	b	2a194 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x774>
   2adf0:	29578e64 	ldp	w4, w3, [x19, #188]
   2adf4:	f94047e0 	ldr	x0, [sp, #136]
   2adf8:	f106005f 	cmp	x2, #0x180
   2adfc:	9100c261 	add	x1, x19, #0x30
   2ae00:	aa1c03e2 	mov	x2, x28
   2ae04:	a9187fff 	stp	xzr, xzr, [sp, #384]
   2ae08:	f900cbff 	str	xzr, [sp, #400]
   2ae0c:	1a841484 	cinc	w4, w4, eq  // eq = none
   2ae10:	11000463 	add	w3, w3, #0x1
   2ae14:	29178e64 	stp	w4, w3, [x19, #188]
   2ae18:	97fff592 	bl	28460 <NativeMG::Impl::coarse_schur(std::vector<float, lqcd_native::WorkspaceAllocator<float> > const&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&) const>
   2ae1c:	91006276 	add	x22, x19, #0x18
   2ae20:	aa1303e1 	mov	x1, x19
   2ae24:	aa1603e0 	mov	x0, x22
   2ae28:	97ffee5e 	bl	267a0 <std::vector<float, lqcd_native::WorkspaceAllocator<float> >::operator=(std::vector<float, lqcd_native::WorkspaceAllocator<float> > const&) [clone .isra.0]>
   2ae2c:	aa1c03e1 	mov	x1, x28
   2ae30:	1e604100 	fmov	d0, d8
   2ae34:	aa1603e0 	mov	x0, x22
   2ae38:	2f00e401 	movi	d1, #0x0
   2ae3c:	97ff8a3d 	bl	d730 <lqcd_native::detail::coarse_axpy(std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::complex<double>, std::vector<float, lqcd_native::WorkspaceAllocator<float> > const&)>
   2ae40:	a95703e1 	ldp	x1, x0, [sp, #368]
   2ae44:	eb00003f 	cmp	x1, x0
   2ae48:	54000780 	b.eq	2af38 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1518>  // b.none
   2ae4c:	b9414fe0 	ldr	w0, [sp, #332]
   2ae50:	b8004420 	str	w0, [x1], #4
   2ae54:	f900bbe1 	str	x1, [sp, #368]
   2ae58:	f940c3e0 	ldr	x0, [sp, #384]
   2ae5c:	b4ffc080 	cbz	x0, 2a66c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xc4c>
   2ae60:	97ff6888 	bl	5080 <free@plt>
   2ae64:	17fffe02 	b	2a66c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xc4c>
   2ae68:	b00002a0 	adrp	x0, 7f000 <__FRAME_END__+0x1ea64>
   2ae6c:	f9475800 	ldr	x0, [x0, #3760]
   2ae70:	b9400000 	ldr	w0, [x0]
   2ae74:	7100041f 	cmp	w0, #0x1
   2ae78:	54fff32c 	b.gt	2acdc <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x12bc>
   2ae7c:	b94093e0 	ldr	w0, [sp, #144]
   2ae80:	b900dbe0 	str	w0, [sp, #216]
   2ae84:	17fffd32 	b	2a34c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x92c>
   2ae88:	91018262 	add	x2, x19, #0x60
   2ae8c:	94000629 	bl	2c730 <void std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >::_M_realloc_insert<std::vector<float, lqcd_native::WorkspaceAllocator<float> > >(__gnu_cxx::__normal_iterator<std::vector<float, lqcd_native::WorkspaceAllocator<float> >*, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > >, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&&)>
   2ae90:	f9404e62 	ldr	x2, [x19, #152]
   2ae94:	17fffdec 	b	2a644 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xc24>
   2ae98:	91012262 	add	x2, x19, #0x48
   2ae9c:	94000625 	bl	2c730 <void std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >::_M_realloc_insert<std::vector<float, lqcd_native::WorkspaceAllocator<float> > >(__gnu_cxx::__normal_iterator<std::vector<float, lqcd_native::WorkspaceAllocator<float> >*, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > >, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&&)>
   2aea0:	17fffddc 	b	2a610 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xbf0>
   2aea4:	b940dbe0 	ldr	w0, [sp, #216]
   2aea8:	11000800 	add	w0, w0, #0x2
   2aeac:	b900dbe0 	str	w0, [sp, #216]
   2aeb0:	17fffe47 	b	2a7cc <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xdac>
   2aeb4:	f94087e0 	ldr	x0, [sp, #264]
   2aeb8:	aa1303e1 	mov	x1, x19
   2aebc:	aa1903e2 	mov	x2, x25
   2aec0:	97ff6840 	bl	4fc0 <void std::vector<int, std::allocator<int> >::_M_realloc_insert<int const&>(__gnu_cxx::__normal_iterator<int*, std::vector<int, std::allocator<int> > >, int const&)@plt>
   2aec4:	17ffff9d 	b	2ad38 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1318>
   2aec8:	f94077e0 	ldr	x0, [sp, #232]
   2aecc:	eb00029f 	cmp	x20, x0
   2aed0:	54ffe6c1 	b.ne	2aba8 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1188>  // b.any
   2aed4:	17ffff68 	b	2ac74 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1254>
   2aed8:	b00002a5 	adrp	x5, 7f000 <__FRAME_END__+0x1ea64>
   2aedc:	b00002a4 	adrp	x4, 7f000 <__FRAME_END__+0x1ea64>
   2aee0:	b00002a3 	adrp	x3, 7f000 <__FRAME_END__+0x1ea64>
   2aee4:	b94113e2 	ldr	w2, [sp, #272]
   2aee8:	f94760a5 	ldr	x5, [x5, #3776]
   2aeec:	f9474884 	ldr	x4, [x4, #3728]
   2aef0:	d2800020 	mov	x0, #0x1                   	// #1
   2aef4:	f9478063 	ldr	x3, [x3, #3840]
   2aef8:	f94067e1 	ldr	x1, [sp, #200]
   2aefc:	f94000a5 	ldr	x5, [x5]
   2af00:	97ff6918 	bl	5360 <MPI_Allreduce@plt>
   2af04:	17fffd48 	b	2a424 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xa04>
   2af08:	b00002a5 	adrp	x5, 7f000 <__FRAME_END__+0x1ea64>
   2af0c:	b00002a4 	adrp	x4, 7f000 <__FRAME_END__+0x1ea64>
   2af10:	b00002a3 	adrp	x3, 7f000 <__FRAME_END__+0x1ea64>
   2af14:	b940fbe2 	ldr	w2, [sp, #248]
   2af18:	f94760a5 	ldr	x5, [x5, #3776]
   2af1c:	f9474884 	ldr	x4, [x4, #3728]
   2af20:	d2800020 	mov	x0, #0x1                   	// #1
   2af24:	f9478063 	ldr	x3, [x3, #3840]
   2af28:	f94057e1 	ldr	x1, [sp, #168]
   2af2c:	f94000a5 	ldr	x5, [x5]
   2af30:	97ff690c 	bl	5360 <MPI_Allreduce@plt>
   2af34:	17fffd93 	b	2a580 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xb60>
   2af38:	f9408fe0 	ldr	x0, [sp, #280]
   2af3c:	aa1803e2 	mov	x2, x24
   2af40:	97ff6820 	bl	4fc0 <void std::vector<int, std::allocator<int> >::_M_realloc_insert<int const&>(__gnu_cxx::__normal_iterator<int*, std::vector<int, std::allocator<int> > >, int const&)@plt>
   2af44:	17ffffc5 	b	2ae58 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1438>
   2af48:	b00002a5 	adrp	x5, 7f000 <__FRAME_END__+0x1ea64>
   2af4c:	b00002a4 	adrp	x4, 7f000 <__FRAME_END__+0x1ea64>
   2af50:	b00002a3 	adrp	x3, 7f000 <__FRAME_END__+0x1ea64>
   2af54:	b940fbe2 	ldr	w2, [sp, #248]
   2af58:	f94760a5 	ldr	x5, [x5, #3776]
   2af5c:	f9474884 	ldr	x4, [x4, #3728]
   2af60:	d2800020 	mov	x0, #0x1                   	// #1
   2af64:	f9478063 	ldr	x3, [x3, #3840]
   2af68:	f94057e1 	ldr	x1, [sp, #168]
   2af6c:	f94000a5 	ldr	x5, [x5]
   2af70:	97ff68fc 	bl	5360 <MPI_Allreduce@plt>
   2af74:	17fffde5 	b	2a708 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xce8>
   2af78:	97ff685a 	bl	50e0 <omp_in_parallel@plt>
   2af7c:	7100001f 	cmp	w0, #0x0
   2af80:	7a560260 	ccmp	w19, w22, #0x0, eq  // eq = none
   2af84:	1a9fc7e0 	cset	w0, le
   2af88:	6b16027f 	cmp	w19, w22
   2af8c:	1a9f07e1 	cset	w1, ne  // ne = any
   2af90:	6a000020 	ands	w0, w1, w0
   2af94:	b90123e0 	str	w0, [sp, #288]
   2af98:	54ff5e60 	b.eq	29b64 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x144>  // b.none
   2af9c:	2a1303e0 	mov	w0, w19
   2afa0:	97ff68c8 	bl	52c0 <omp_set_num_threads@plt>
   2afa4:	b9409fe1 	ldr	w1, [sp, #156]
   2afa8:	52801900 	mov	w0, #0xc8                  	// #200
   2afac:	9b207c20 	smull	x0, w1, w0
   2afb0:	f90083e0 	str	x0, [sp, #256]
   2afb4:	97ff68a3 	bl	5240 <operator new(unsigned long)@plt>
   2afb8:	aa0003fb 	mov	x27, x0
   2afbc:	17fffaf1 	b	29b80 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x160>
   2afc0:	b00002a5 	adrp	x5, 7f000 <__FRAME_END__+0x1ea64>
   2afc4:	b00002a4 	adrp	x4, 7f000 <__FRAME_END__+0x1ea64>
   2afc8:	b00002a3 	adrp	x3, 7f000 <__FRAME_END__+0x1ea64>
   2afcc:	f94073e0 	ldr	x0, [sp, #224]
   2afd0:	f94760a5 	ldr	x5, [x5, #3776]
   2afd4:	f9474884 	ldr	x4, [x4, #3728]
   2afd8:	f9478063 	ldr	x3, [x3, #3840]
   2afdc:	f94057e1 	ldr	x1, [sp, #168]
   2afe0:	d3438802 	ubfx	x2, x0, #3, #32
   2afe4:	d2800020 	mov	x0, #0x1                   	// #1
   2afe8:	f94000a5 	ldr	x5, [x5]
   2afec:	97ff68dd 	bl	5360 <MPI_Allreduce@plt>
   2aff0:	17fffb43 	b	29cfc <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x2dc>
   2aff4:	b00002a5 	adrp	x5, 7f000 <__FRAME_END__+0x1ea64>
   2aff8:	b00002a4 	adrp	x4, 7f000 <__FRAME_END__+0x1ea64>
   2affc:	b00002a3 	adrp	x3, 7f000 <__FRAME_END__+0x1ea64>
   2b000:	f94073e0 	ldr	x0, [sp, #224]
   2b004:	f94760a5 	ldr	x5, [x5, #3776]
   2b008:	f9474884 	ldr	x4, [x4, #3728]
   2b00c:	f9478063 	ldr	x3, [x3, #3840]
   2b010:	f94057e1 	ldr	x1, [sp, #168]
   2b014:	d3438802 	ubfx	x2, x0, #3, #32
   2b018:	d2800020 	mov	x0, #0x1                   	// #1
   2b01c:	f94000a5 	ldr	x5, [x5]
   2b020:	97ff68d0 	bl	5360 <MPI_Allreduce@plt>
   2b024:	17fffba9 	b	29ec8 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x4a8>
   2b028:	f94063e0 	ldr	x0, [sp, #192]
   2b02c:	9103e362 	add	x2, x27, #0xf8
   2b030:	f9400003 	ldr	x3, [x0]
   2b034:	f9405be0 	ldr	x0, [sp, #176]
   2b038:	f9400001 	ldr	x1, [x0]
   2b03c:	f94047e0 	ldr	x0, [sp, #136]
   2b040:	91006063 	add	x3, x3, #0x18
   2b044:	91006021 	add	x1, x1, #0x18
   2b048:	97fff48e 	bl	28280 <NativeMG::Impl::coarse_reconstruct(std::vector<float, lqcd_native::WorkspaceAllocator<float> > const&, std::vector<float, lqcd_native::WorkspaceAllocator<float> > const&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&) const>
   2b04c:	17fffdee 	b	2a804 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xde4>
   2b050:	f94063e0 	ldr	x0, [sp, #192]
   2b054:	f94097e2 	ldr	x2, [sp, #296]
   2b058:	f9400003 	ldr	x3, [x0]
   2b05c:	f9405be0 	ldr	x0, [sp, #176]
   2b060:	f9400001 	ldr	x1, [x0]
   2b064:	f94047e0 	ldr	x0, [sp, #136]
   2b068:	97fff486 	bl	28280 <NativeMG::Impl::coarse_reconstruct(std::vector<float, lqcd_native::WorkspaceAllocator<float> > const&, std::vector<float, lqcd_native::WorkspaceAllocator<float> > const&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&) const>
   2b06c:	17fffde2 	b	2a7f4 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xdd4>
   2b070:	a94e0b65 	ldp	x5, x2, [x27, #224]
   2b074:	d2835004 	mov	x4, #0x1a80                	// #6784
   2b078:	91038360 	add	x0, x27, #0xe0
   2b07c:	52800003 	mov	w3, #0x0                   	// #0
   2b080:	f2a000c4 	movk	x4, #0x6, lsl #16
   2b084:	f900c3e0 	str	x0, [sp, #384]
   2b088:	b0ffffc0 	adrp	x0, 24000 <(anonymous namespace)::coarse_gcr_fused_step(std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, double&) [clone ._omp_fn.1]+0x1a0>
   2b08c:	aa1c03e1 	mov	x1, x28
   2b090:	91280000 	add	x0, x0, #0xa00
   2b094:	f900c7ff 	str	xzr, [sp, #392]
   2b098:	cb050042 	sub	x2, x2, x5
   2b09c:	eb04005f 	cmp	x2, x4
   2b0a0:	1a9f87e2 	cset	w2, ls  // ls = plast
   2b0a4:	97ff692b 	bl	5550 <GOMP_parallel@plt>
   2b0a8:	fd40c7e0 	ldr	d0, [sp, #392]
   2b0ac:	f94057e0 	ldr	x0, [sp, #168]
   2b0b0:	fd000400 	str	d0, [x0, #8]
   2b0b4:	17fffb3b 	b	29da0 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x380>
   2b0b8:	a9418b65 	ldp	x5, x2, [x27, #24]
   2b0bc:	d2835004 	mov	x4, #0x1a80                	// #6784
   2b0c0:	91006360 	add	x0, x27, #0x18
   2b0c4:	52800003 	mov	w3, #0x0                   	// #0
   2b0c8:	f2a000c4 	movk	x4, #0x6, lsl #16
   2b0cc:	f900c3e0 	str	x0, [sp, #384]
   2b0d0:	b0ffffc0 	adrp	x0, 24000 <(anonymous namespace)::coarse_gcr_fused_step(std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, double&) [clone ._omp_fn.1]+0x1a0>
   2b0d4:	aa1c03e1 	mov	x1, x28
   2b0d8:	91280000 	add	x0, x0, #0xa00
   2b0dc:	f900c7ff 	str	xzr, [sp, #392]
   2b0e0:	cb050042 	sub	x2, x2, x5
   2b0e4:	eb04005f 	cmp	x2, x4
   2b0e8:	1a9f87e2 	cset	w2, ls  // ls = plast
   2b0ec:	97ff6919 	bl	5550 <GOMP_parallel@plt>
   2b0f0:	fd40c7e0 	ldr	d0, [sp, #392]
   2b0f4:	f94057e0 	ldr	x0, [sp, #168]
   2b0f8:	fd000000 	str	d0, [x0]
   2b0fc:	17fffb25 	b	29d90 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x370>
   2b100:	a95a8b65 	ldp	x5, x2, [x27, #424]
   2b104:	d2835004 	mov	x4, #0x1a80                	// #6784
   2b108:	9106a360 	add	x0, x27, #0x1a8
   2b10c:	52800003 	mov	w3, #0x0                   	// #0
   2b110:	f2a000c4 	movk	x4, #0x6, lsl #16
   2b114:	f900c3e0 	str	x0, [sp, #384]
   2b118:	b0ffffc0 	adrp	x0, 24000 <(anonymous namespace)::coarse_gcr_fused_step(std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, double&) [clone ._omp_fn.1]+0x1a0>
   2b11c:	aa1c03e1 	mov	x1, x28
   2b120:	91280000 	add	x0, x0, #0xa00
   2b124:	f900c7ff 	str	xzr, [sp, #392]
   2b128:	cb050042 	sub	x2, x2, x5
   2b12c:	eb04005f 	cmp	x2, x4
   2b130:	1a9f87e2 	cset	w2, ls  // ls = plast
   2b134:	97ff6907 	bl	5550 <GOMP_parallel@plt>
   2b138:	fd40c7e0 	ldr	d0, [sp, #392]
   2b13c:	f94057e0 	ldr	x0, [sp, #168]
   2b140:	fd000800 	str	d0, [x0, #16]
   2b144:	17fffb1c 	b	29db4 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x394>
   2b148:	f94047e0 	ldr	x0, [sp, #136]
   2b14c:	6d4006a0 	ldp	d0, d1, [x21]
   2b150:	fd44e402 	ldr	d2, [x0, #2504]
   2b154:	1e620800 	fmul	d0, d0, d2
   2b158:	1e612010 	fcmpe	d0, d1
   2b15c:	1a9f87fc 	cset	w28, ls  // ls = plast
   2b160:	35ffcad4 	cbnz	w20, 2aab8 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1098>
   2b164:	d2800002 	mov	x2, #0x0                   	// #0
   2b168:	f94043e1 	ldr	x1, [sp, #128]
   2b16c:	17fffe55 	b	2aac0 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x10a0>
   2b170:	f94063e0 	ldr	x0, [sp, #192]
   2b174:	91070362 	add	x2, x27, #0x1c0
   2b178:	f9400003 	ldr	x3, [x0]
   2b17c:	f9405be0 	ldr	x0, [sp, #176]
   2b180:	f9400001 	ldr	x1, [x0]
   2b184:	f94047e0 	ldr	x0, [sp, #136]
   2b188:	9100c063 	add	x3, x3, #0x30
   2b18c:	9100c021 	add	x1, x1, #0x30
   2b190:	97fff43c 	bl	28280 <NativeMG::Impl::coarse_reconstruct(std::vector<float, lqcd_native::WorkspaceAllocator<float> > const&, std::vector<float, lqcd_native::WorkspaceAllocator<float> > const&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&) const>
   2b194:	17fffda2 	b	2a81c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xdfc>
   2b198:	5280001c 	mov	w28, #0x0                   	// #0
   2b19c:	17fffe46 	b	2aab4 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1094>
   2b1a0:	1e61c000 	fsqrt	d0, d0
   2b1a4:	17fffb6d 	b	29f58 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x538>
   2b1a8:	1e61c000 	fsqrt	d0, d0
   2b1ac:	17fffb74 	b	29f7c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x55c>
   2b1b0:	1e61c000 	fsqrt	d0, d0
   2b1b4:	17fffb7b 	b	29fa0 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x580>
   2b1b8:	b000017c 	adrp	x28, 58000 <typeinfo name for lqcd::Error+0x88>
   2b1bc:	9102e375 	add	x21, x27, #0xb8
   2b1c0:	52800014 	mov	w20, #0x0                   	// #0
   2b1c4:	9132c380 	add	x0, x28, #0xcb0
   2b1c8:	f90043e0 	str	x0, [sp, #128]
   2b1cc:	1400000d 	b	2b200 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x17e0>
   2b1d0:	d2800022 	mov	x2, #0x1                   	// #1
   2b1d4:	aa1703e1 	mov	x1, x23
   2b1d8:	f947de60 	ldr	x0, [x19, #4024]
   2b1dc:	97ff6845 	bl	52f0 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2b1e0:	f947de60 	ldr	x0, [x19, #4024]
   2b1e4:	2a1c03e1 	mov	w1, w28
   2b1e8:	97ff693a 	bl	56d0 <std::ostream::operator<<(int)@plt>
   2b1ec:	b9409fe0 	ldr	w0, [sp, #156]
   2b1f0:	11000694 	add	w20, w20, #0x1
   2b1f4:	910322b5 	add	x21, x21, #0xc8
   2b1f8:	6b14001f 	cmp	w0, w20
   2b1fc:	54ffc76d 	b.le	2aae8 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x10c8>
   2b200:	b94002bc 	ldr	w28, [x21]
   2b204:	35fffe74 	cbnz	w20, 2b1d0 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x17b0>
   2b208:	d2800002 	mov	x2, #0x0                   	// #0
   2b20c:	f94043e1 	ldr	x1, [sp, #128]
   2b210:	17fffff2 	b	2b1d8 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x17b8>
   2b214:	1e61c000 	fsqrt	d0, d0
   2b218:	17fffb6b 	b	29fc4 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x5a4>
   2b21c:	6d4627e8 	ldp	d8, d9, [sp, #96]
   2b220:	fd403bea 	ldr	d10, [sp, #112]
   2b224:	b94127e0 	ldr	w0, [sp, #292]
   2b228:	a94153f3 	ldp	x19, x20, [sp, #16]
   2b22c:	a9425bf5 	ldp	x21, x22, [sp, #32]
   2b230:	a94363f7 	ldp	x23, x24, [sp, #48]
   2b234:	a9446bf9 	ldp	x25, x26, [sp, #64]
   2b238:	a94573fb 	ldp	x27, x28, [sp, #80]
   2b23c:	a8dc7bfd 	ldp	x29, x30, [sp], #448
   2b240:	17ff6820 	b	52c0 <omp_set_num_threads@plt>
   2b244:	1e61c000 	fsqrt	d0, d0
   2b248:	17fffb71 	b	2a00c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x5ec>
   2b24c:	1e61c000 	fsqrt	d0, d0
   2b250:	17fffb66 	b	29fe8 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x5c8>
   2b254:	f947de61 	ldr	x1, [x19, #4024]
   2b258:	f9400020 	ldr	x0, [x1]
   2b25c:	f85e8000 	ldur	x0, [x0, #-24]
   2b260:	8b010000 	add	x0, x0, x1
   2b264:	b9402001 	ldr	w1, [x0, #32]
   2b268:	32000021 	orr	w1, w1, #0x1
   2b26c:	97ff690d 	bl	56a0 <std::basic_ios<char, std::char_traits<char> >::clear(std::_Ios_Iostate)@plt>
   2b270:	17fffdfb 	b	2aa5c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x103c>
   2b274:	1e61c000 	fsqrt	d0, d0
   2b278:	17fffb6e 	b	2a030 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x610>
   2b27c:	1e61c000 	fsqrt	d0, d0
   2b280:	17fffb75 	b	2a054 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x634>
   2b284:	f94067e0 	ldr	x0, [sp, #200]
   2b288:	f9407be2 	ldr	x2, [sp, #240]
   2b28c:	52800001 	mov	w1, #0x0                   	// #0
   2b290:	97ff6784 	bl	50a0 <memset@plt>
   2b294:	17fffc3c 	b	2a384 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x964>
   2b298:	f9413b65 	ldr	x5, [x27, #624]
   2b29c:	f9413f62 	ldr	x2, [x27, #632]
   2b2a0:	d2835004 	mov	x4, #0x1a80                	// #6784
   2b2a4:	9109c360 	add	x0, x27, #0x270
   2b2a8:	f2a000c4 	movk	x4, #0x6, lsl #16
   2b2ac:	f900c3e0 	str	x0, [sp, #384]
   2b2b0:	b0ffffc0 	adrp	x0, 24000 <(anonymous namespace)::coarse_gcr_fused_step(std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, double&) [clone ._omp_fn.1]+0x1a0>
   2b2b4:	52800003 	mov	w3, #0x0                   	// #0
   2b2b8:	91280000 	add	x0, x0, #0xa00
   2b2bc:	aa1c03e1 	mov	x1, x28
   2b2c0:	f900c7ff 	str	xzr, [sp, #392]
   2b2c4:	cb050042 	sub	x2, x2, x5
   2b2c8:	eb04005f 	cmp	x2, x4
   2b2cc:	1a9f87e2 	cset	w2, ls  // ls = plast
   2b2d0:	97ff68a0 	bl	5550 <GOMP_parallel@plt>
   2b2d4:	fd40c7e0 	ldr	d0, [sp, #392]
   2b2d8:	f94057e0 	ldr	x0, [sp, #168]
   2b2dc:	fd000c00 	str	d0, [x0, #24]
   2b2e0:	17fffaba 	b	29dc8 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x3a8>
   2b2e4:	b0000160 	adrp	x0, 58000 <typeinfo name for lqcd::Error+0x88>
   2b2e8:	52800001 	mov	w1, #0x0                   	// #0
   2b2ec:	91262000 	add	x0, x0, #0x988
   2b2f0:	97ff882c 	bl	d3a0 <lqcd_native::detail::setting(char const*, int)>
   2b2f4:	34001120 	cbz	w0, 2b518 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1af8>
   2b2f8:	900002a0 	adrp	x0, 7f000 <__FRAME_END__+0x1ea64>
   2b2fc:	f947c800 	ldr	x0, [x0, #3984]
   2b300:	b9400000 	ldr	w0, [x0]
   2b304:	350010a0 	cbnz	w0, 2b518 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1af8>
   2b308:	900002b3 	adrp	x19, 7f000 <__FRAME_END__+0x1ea64>
   2b30c:	b0000161 	adrp	x1, 58000 <typeinfo name for lqcd::Error+0x88>
   2b310:	d2800462 	mov	x2, #0x23                  	// #35
   2b314:	f947de60 	ldr	x0, [x19, #4024]
   2b318:	91266021 	add	x1, x1, #0x998
   2b31c:	97ff67f5 	bl	52f0 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2b320:	f947de60 	ldr	x0, [x19, #4024]
   2b324:	b9409fe1 	ldr	w1, [sp, #156]
   2b328:	97ff68ea 	bl	56d0 <std::ostream::operator<<(int)@plt>
   2b32c:	b0000161 	adrp	x1, 58000 <typeinfo name for lqcd::Error+0x88>
   2b330:	d2800262 	mov	x2, #0x13                  	// #19
   2b334:	aa0003f4 	mov	x20, x0
   2b338:	91270021 	add	x1, x1, #0x9c0
   2b33c:	97ff67ed 	bl	52f0 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2b340:	f94047f5 	ldr	x21, [sp, #136]
   2b344:	aa1403e0 	mov	x0, x20
   2b348:	b94adaa1 	ldr	w1, [x21, #2776]
   2b34c:	97ff68e1 	bl	56d0 <std::ostream::operator<<(int)@plt>
   2b350:	b0000161 	adrp	x1, 58000 <typeinfo name for lqcd::Error+0x88>
   2b354:	d2800282 	mov	x2, #0x14                  	// #20
   2b358:	aa0003f4 	mov	x20, x0
   2b35c:	91276021 	add	x1, x1, #0x9d8
   2b360:	97ff67e4 	bl	52f0 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2b364:	fd44e6a0 	ldr	d0, [x21, #2504]
   2b368:	aa1403e0 	mov	x0, x20
   2b36c:	97ff68a5 	bl	5600 <std::ostream& std::ostream::_M_insert<double>(double)@plt>
   2b370:	b0000161 	adrp	x1, 58000 <typeinfo name for lqcd::Error+0x88>
   2b374:	d2800282 	mov	x2, #0x14                  	// #20
   2b378:	aa0003f4 	mov	x20, x0
   2b37c:	9127c021 	add	x1, x1, #0x9f0
   2b380:	97ff67dc 	bl	52f0 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2b384:	aa1403e0 	mov	x0, x20
   2b388:	52800021 	mov	w1, #0x1                   	// #1
   2b38c:	97ff68d1 	bl	56d0 <std::ostream::operator<<(int)@plt>
   2b390:	b0000161 	adrp	x1, 58000 <typeinfo name for lqcd::Error+0x88>
   2b394:	d2800262 	mov	x2, #0x13                  	// #19
   2b398:	aa0003f4 	mov	x20, x0
   2b39c:	91282021 	add	x1, x1, #0xa08
   2b3a0:	97ff67d4 	bl	52f0 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2b3a4:	900002a0 	adrp	x0, 7f000 <__FRAME_END__+0x1ea64>
   2b3a8:	f9475801 	ldr	x1, [x0, #3760]
   2b3ac:	aa1403e0 	mov	x0, x20
   2b3b0:	b9400021 	ldr	w1, [x1]
   2b3b4:	7100043f 	cmp	w1, #0x1
   2b3b8:	1a9fd7e1 	cset	w1, gt
   2b3bc:	97ff68c5 	bl	56d0 <std::ostream::operator<<(int)@plt>
   2b3c0:	b00002a0 	adrp	x0, 80000 <std::ostream::put(char)@GLIBCXX_3.4>
   2b3c4:	b000017a 	adrp	x26, 58000 <typeinfo name for lqcd::Error+0x88>
   2b3c8:	b0000175 	adrp	x21, 58000 <typeinfo name for lqcd::Error+0x88>
   2b3cc:	9117c000 	add	x0, x0, #0x5f0
   2b3d0:	aa1c03f7 	mov	x23, x28
   2b3d4:	9128a35a 	add	x26, x26, #0xa28
   2b3d8:	4c40a000 	ld1	{v0.16b, v1.16b}, [x0]
   2b3dc:	912522b5 	add	x21, x21, #0x948
   2b3e0:	52800014 	mov	w20, #0x0                   	// #0
   2b3e4:	b0000179 	adrp	x25, 58000 <typeinfo name for lqcd::Error+0x88>
   2b3e8:	4c00a380 	st1	{v0.16b, v1.16b}, [x28]
   2b3ec:	f947de60 	ldr	x0, [x19, #4024]
   2b3f0:	d2800042 	mov	x2, #0x2                   	// #2
   2b3f4:	91288321 	add	x1, x25, #0xa20
   2b3f8:	97ff67be 	bl	52f0 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2b3fc:	f94002f6 	ldr	x22, [x23]
   2b400:	b4003436 	cbz	x22, 2ba84 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x2064>
   2b404:	aa1603e0 	mov	x0, x22
   2b408:	97ff66da 	bl	4f70 <strlen@plt>
   2b40c:	aa0003e2 	mov	x2, x0
   2b410:	f947de60 	ldr	x0, [x19, #4024]
   2b414:	aa1603e1 	mov	x1, x22
   2b418:	97ff67b6 	bl	52f0 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2b41c:	f947de60 	ldr	x0, [x19, #4024]
   2b420:	d2800062 	mov	x2, #0x3                   	// #3
   2b424:	aa1a03e1 	mov	x1, x26
   2b428:	97ff67b2 	bl	52f0 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2b42c:	b0000160 	adrp	x0, 58000 <typeinfo name for lqcd::Error+0x88>
   2b430:	34002ff4 	cbz	w20, 2ba2c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x200c>
   2b434:	7100069f 	cmp	w20, #0x1
   2b438:	540035c0 	b.eq	2baf0 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x20d0>  // b.none
   2b43c:	71000a9f 	cmp	w20, #0x2
   2b440:	540039e0 	b.eq	2bb7c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x215c>  // b.none
   2b444:	9132c000 	add	x0, x0, #0xcb0
   2b448:	9102a376 	add	x22, x27, #0xa8
   2b44c:	52800018 	mov	w24, #0x0                   	// #0
   2b450:	f90043e0 	str	x0, [sp, #128]
   2b454:	394072c0 	ldrb	w0, [x22, #28]
   2b458:	35000f60 	cbnz	w0, 2b644 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1c24>
   2b45c:	f94047e1 	ldr	x1, [sp, #136]
   2b460:	b94012c0 	ldr	w0, [x22, #16]
   2b464:	5280001c 	mov	w28, #0x0                   	// #0
   2b468:	b94ad821 	ldr	w1, [x1, #2776]
   2b46c:	6b00003f 	cmp	w1, w0
   2b470:	54000c40 	b.eq	2b5f8 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1bd8>  // b.none
   2b474:	34000ed8 	cbz	w24, 2b64c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1c2c>
   2b478:	d2800022 	mov	x2, #0x1                   	// #1
   2b47c:	aa1503e1 	mov	x1, x21
   2b480:	f947de60 	ldr	x0, [x19, #4024]
   2b484:	97ff679b 	bl	52f0 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2b488:	f947de60 	ldr	x0, [x19, #4024]
   2b48c:	2a1c03e1 	mov	w1, w28
   2b490:	97ff6890 	bl	56d0 <std::ostream::operator<<(int)@plt>
   2b494:	b9409fe0 	ldr	w0, [sp, #156]
   2b498:	11000718 	add	w24, w24, #0x1
   2b49c:	910322d6 	add	x22, x22, #0xc8
   2b4a0:	6b18001f 	cmp	w0, w24
   2b4a4:	54fffd8c 	b.gt	2b454 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1a34>
   2b4a8:	f947de60 	ldr	x0, [x19, #4024]
   2b4ac:	52800ba3 	mov	w3, #0x5d                  	// #93
   2b4b0:	d2800022 	mov	x2, #0x1                   	// #1
   2b4b4:	9105a3e1 	add	x1, sp, #0x168
   2b4b8:	3905a3e3 	strb	w3, [sp, #360]
   2b4bc:	97ff678d 	bl	52f0 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2b4c0:	11000694 	add	w20, w20, #0x1
   2b4c4:	910022f7 	add	x23, x23, #0x8
   2b4c8:	7100129f 	cmp	w20, #0x4
   2b4cc:	54fff901 	b.ne	2b3ec <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x19cc>  // b.any
   2b4d0:	f947de60 	ldr	x0, [x19, #4024]
   2b4d4:	52800fa3 	mov	w3, #0x7d                  	// #125
   2b4d8:	d2800022 	mov	x2, #0x1                   	// #1
   2b4dc:	910543e1 	add	x1, sp, #0x150
   2b4e0:	390543e3 	strb	w3, [sp, #336]
   2b4e4:	97ff6783 	bl	52f0 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2b4e8:	aa0003f3 	mov	x19, x0
   2b4ec:	f9400000 	ldr	x0, [x0]
   2b4f0:	f85e8000 	ldur	x0, [x0, #-24]
   2b4f4:	8b000260 	add	x0, x19, x0
   2b4f8:	f9407814 	ldr	x20, [x0, #240]
   2b4fc:	b40037f4 	cbz	x20, 2bbf8 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x21d8>
   2b500:	3940e280 	ldrb	w0, [x20, #56]
   2b504:	34003220 	cbz	w0, 2bb48 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x2128>
   2b508:	39410e81 	ldrb	w1, [x20, #67]
   2b50c:	aa1303e0 	mov	x0, x19
   2b510:	97ff6658 	bl	4e70 <std::ostream::put(char)@plt>
   2b514:	97ff670f 	bl	5150 <std::ostream::flush()@plt>
   2b518:	f94057e0 	ldr	x0, [sp, #168]
   2b51c:	f94073e1 	ldr	x1, [sp, #224]
   2b520:	aa1b03f4 	mov	x20, x27
   2b524:	97ff674b 	bl	5250 <operator delete(void*, unsigned long)@plt>
   2b528:	a9495693 	ldp	x19, x21, [x20, #144]
   2b52c:	eb15027f 	cmp	x19, x21
   2b530:	54000120 	b.eq	2b554 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1b34>  // b.none
   2b534:	d503201f 	nop
   2b538:	f9400260 	ldr	x0, [x19]
   2b53c:	91006273 	add	x19, x19, #0x18
   2b540:	b4000720 	cbz	x0, 2b624 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1c04>
   2b544:	97ff66cf 	bl	5080 <free@plt>
   2b548:	eb1302bf 	cmp	x21, x19
   2b54c:	54ffff61 	b.ne	2b538 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1b18>  // b.any
   2b550:	f9404a95 	ldr	x21, [x20, #144]
   2b554:	b40000b5 	cbz	x21, 2b568 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1b48>
   2b558:	f9405281 	ldr	x1, [x20, #160]
   2b55c:	aa1503e0 	mov	x0, x21
   2b560:	cb150021 	sub	x1, x1, x21
   2b564:	97ff673b 	bl	5250 <operator delete(void*, unsigned long)@plt>
   2b568:	a947d693 	ldp	x19, x21, [x20, #120]
   2b56c:	eb15027f 	cmp	x19, x21
   2b570:	54000120 	b.eq	2b594 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1b74>  // b.none
   2b574:	d503201f 	nop
   2b578:	f9400260 	ldr	x0, [x19]
   2b57c:	91006273 	add	x19, x19, #0x18
   2b580:	b40004a0 	cbz	x0, 2b614 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1bf4>
   2b584:	97ff66bf 	bl	5080 <free@plt>
   2b588:	eb1302bf 	cmp	x21, x19
   2b58c:	54ffff61 	b.ne	2b578 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1b58>  // b.any
   2b590:	f9403e95 	ldr	x21, [x20, #120]
   2b594:	b40000b5 	cbz	x21, 2b5a8 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1b88>
   2b598:	f9404681 	ldr	x1, [x20, #136]
   2b59c:	aa1503e0 	mov	x0, x21
   2b5a0:	cb150021 	sub	x1, x1, x21
   2b5a4:	97ff672b 	bl	5250 <operator delete(void*, unsigned long)@plt>
   2b5a8:	f9403280 	ldr	x0, [x20, #96]
   2b5ac:	b4000040 	cbz	x0, 2b5b4 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1b94>
   2b5b0:	97ff66b4 	bl	5080 <free@plt>
   2b5b4:	f9402680 	ldr	x0, [x20, #72]
   2b5b8:	b4000040 	cbz	x0, 2b5c0 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1ba0>
   2b5bc:	97ff66b1 	bl	5080 <free@plt>
   2b5c0:	f9401a80 	ldr	x0, [x20, #48]
   2b5c4:	b4000040 	cbz	x0, 2b5cc <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1bac>
   2b5c8:	97ff66ae 	bl	5080 <free@plt>
   2b5cc:	f9400e80 	ldr	x0, [x20, #24]
   2b5d0:	b4000040 	cbz	x0, 2b5d8 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1bb8>
   2b5d4:	97ff66ab 	bl	5080 <free@plt>
   2b5d8:	f9400280 	ldr	x0, [x20]
   2b5dc:	91032294 	add	x20, x20, #0xc8
   2b5e0:	b40002a0 	cbz	x0, 2b634 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1c14>
   2b5e4:	97ff66a7 	bl	5080 <free@plt>
   2b5e8:	f94077e0 	ldr	x0, [sp, #232]
   2b5ec:	eb14001f 	cmp	x0, x20
   2b5f0:	54fff9c1 	b.ne	2b528 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1b08>  // b.any
   2b5f4:	17fffda0 	b	2ac74 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1254>
   2b5f8:	f94047e0 	ldr	x0, [sp, #136]
   2b5fc:	6d4006c0 	ldp	d0, d1, [x22]
   2b600:	fd44e402 	ldr	d2, [x0, #2504]
   2b604:	1e620800 	fmul	d0, d0, d2
   2b608:	1e612010 	fcmpe	d0, d1
   2b60c:	1a9f87fc 	cset	w28, ls  // ls = plast
   2b610:	17ffff99 	b	2b474 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1a54>
   2b614:	eb1302bf 	cmp	x21, x19
   2b618:	54fffb01 	b.ne	2b578 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1b58>  // b.any
   2b61c:	f9403e95 	ldr	x21, [x20, #120]
   2b620:	17ffffdd 	b	2b594 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1b74>
   2b624:	eb1302bf 	cmp	x21, x19
   2b628:	54fff881 	b.ne	2b538 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1b18>  // b.any
   2b62c:	f9404a95 	ldr	x21, [x20, #144]
   2b630:	17ffffc9 	b	2b554 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1b34>
   2b634:	f94077e0 	ldr	x0, [sp, #232]
   2b638:	eb00029f 	cmp	x20, x0
   2b63c:	54fff761 	b.ne	2b528 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1b08>  // b.any
   2b640:	17fffd8d 	b	2ac74 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1254>
   2b644:	5280001c 	mov	w28, #0x0                   	// #0
   2b648:	17ffff8b 	b	2b474 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1a54>
   2b64c:	d2800002 	mov	x2, #0x0                   	// #0
   2b650:	f94043e1 	ldr	x1, [sp, #128]
   2b654:	17ffff8b 	b	2b480 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1a60>
   2b658:	1e61c000 	fsqrt	d0, d0
   2b65c:	fd04a760 	str	d0, [x27, #2376]
   2b660:	17fffa87 	b	2a07c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x65c>
   2b664:	f94063e0 	ldr	x0, [sp, #192]
   2b668:	910a2362 	add	x2, x27, #0x288
   2b66c:	f9400003 	ldr	x3, [x0]
   2b670:	f9405be0 	ldr	x0, [sp, #176]
   2b674:	f9400001 	ldr	x1, [x0]
   2b678:	f94047e0 	ldr	x0, [sp, #136]
   2b67c:	91012063 	add	x3, x3, #0x48
   2b680:	91012021 	add	x1, x1, #0x48
   2b684:	97fff2ff 	bl	28280 <NativeMG::Impl::coarse_reconstruct(std::vector<float, lqcd_native::WorkspaceAllocator<float> > const&, std::vector<float, lqcd_native::WorkspaceAllocator<float> > const&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&) const>
   2b688:	17fffc6b 	b	2a834 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xe14>
   2b68c:	f94063e0 	ldr	x0, [sp, #192]
   2b690:	910d4362 	add	x2, x27, #0x350
   2b694:	f9400003 	ldr	x3, [x0]
   2b698:	f9405be0 	ldr	x0, [sp, #176]
   2b69c:	f9400001 	ldr	x1, [x0]
   2b6a0:	f94047e0 	ldr	x0, [sp, #136]
   2b6a4:	91018063 	add	x3, x3, #0x60
   2b6a8:	91018021 	add	x1, x1, #0x60
   2b6ac:	97fff2f5 	bl	28280 <NativeMG::Impl::coarse_reconstruct(std::vector<float, lqcd_native::WorkspaceAllocator<float> > const&, std::vector<float, lqcd_native::WorkspaceAllocator<float> > const&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&) const>
   2b6b0:	17fffc67 	b	2a84c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xe2c>
   2b6b4:	f94063e0 	ldr	x0, [sp, #192]
   2b6b8:	91106362 	add	x2, x27, #0x418
   2b6bc:	f9400003 	ldr	x3, [x0]
   2b6c0:	f9405be0 	ldr	x0, [sp, #176]
   2b6c4:	f9400001 	ldr	x1, [x0]
   2b6c8:	f94047e0 	ldr	x0, [sp, #136]
   2b6cc:	9101e063 	add	x3, x3, #0x78
   2b6d0:	9101e021 	add	x1, x1, #0x78
   2b6d4:	97fff2eb 	bl	28280 <NativeMG::Impl::coarse_reconstruct(std::vector<float, lqcd_native::WorkspaceAllocator<float> > const&, std::vector<float, lqcd_native::WorkspaceAllocator<float> > const&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&) const>
   2b6d8:	17fffc63 	b	2a864 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xe44>
   2b6dc:	f9419f65 	ldr	x5, [x27, #824]
   2b6e0:	f941a362 	ldr	x2, [x27, #832]
   2b6e4:	d2835004 	mov	x4, #0x1a80                	// #6784
   2b6e8:	910ce360 	add	x0, x27, #0x338
   2b6ec:	f2a000c4 	movk	x4, #0x6, lsl #16
   2b6f0:	f900c3e0 	str	x0, [sp, #384]
   2b6f4:	b0ffffc0 	adrp	x0, 24000 <(anonymous namespace)::coarse_gcr_fused_step(std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, double&) [clone ._omp_fn.1]+0x1a0>
   2b6f8:	52800003 	mov	w3, #0x0                   	// #0
   2b6fc:	91280000 	add	x0, x0, #0xa00
   2b700:	aa1c03e1 	mov	x1, x28
   2b704:	f900c7ff 	str	xzr, [sp, #392]
   2b708:	cb050042 	sub	x2, x2, x5
   2b70c:	eb04005f 	cmp	x2, x4
   2b710:	1a9f87e2 	cset	w2, ls  // ls = plast
   2b714:	97ff678f 	bl	5550 <GOMP_parallel@plt>
   2b718:	fd40c7e0 	ldr	d0, [sp, #392]
   2b71c:	f94057e0 	ldr	x0, [sp, #168]
   2b720:	fd001000 	str	d0, [x0, #32]
   2b724:	17fff9ae 	b	29ddc <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x3bc>
   2b728:	f9420365 	ldr	x5, [x27, #1024]
   2b72c:	f9420762 	ldr	x2, [x27, #1032]
   2b730:	d2835004 	mov	x4, #0x1a80                	// #6784
   2b734:	52800003 	mov	w3, #0x0                   	// #0
   2b738:	f2a000c4 	movk	x4, #0x6, lsl #16
   2b73c:	f900c3e0 	str	x0, [sp, #384]
   2b740:	b0ffffc0 	adrp	x0, 24000 <(anonymous namespace)::coarse_gcr_fused_step(std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, double&) [clone ._omp_fn.1]+0x1a0>
   2b744:	aa1c03e1 	mov	x1, x28
   2b748:	91280000 	add	x0, x0, #0xa00
   2b74c:	f900c7ff 	str	xzr, [sp, #392]
   2b750:	cb050042 	sub	x2, x2, x5
   2b754:	eb04005f 	cmp	x2, x4
   2b758:	1a9f87e2 	cset	w2, ls  // ls = plast
   2b75c:	97ff677d 	bl	5550 <GOMP_parallel@plt>
   2b760:	fd40c7e0 	ldr	d0, [sp, #392]
   2b764:	f94057e0 	ldr	x0, [sp, #168]
   2b768:	fd001400 	str	d0, [x0, #40]
   2b76c:	17fff9a2 	b	29df4 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x3d4>
   2b770:	aa1303e0 	mov	x0, x19
   2b774:	97ff66e3 	bl	5300 <std::ctype<char>::_M_widen_init() const@plt>
   2b778:	f9400262 	ldr	x2, [x19]
   2b77c:	90000000 	adrp	x0, 2b000 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x15e0>
   2b780:	52800141 	mov	w1, #0xa                   	// #10
   2b784:	91384000 	add	x0, x0, #0xe10
   2b788:	f9401842 	ldr	x2, [x2, #48]
   2b78c:	eb00005f 	cmp	x2, x0
   2b790:	54ff9de0 	b.eq	2ab4c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x112c>  // b.none
   2b794:	aa1303e0 	mov	x0, x19
   2b798:	d63f0040 	blr	x2
   2b79c:	12001c01 	and	w1, w0, #0xff
   2b7a0:	17fffceb 	b	2ab4c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x112c>
   2b7a4:	b0000160 	adrp	x0, 58000 <typeinfo name for lqcd::Error+0x88>
   2b7a8:	9102f375 	add	x21, x27, #0xbc
   2b7ac:	52800014 	mov	w20, #0x0                   	// #0
   2b7b0:	9132c000 	add	x0, x0, #0xcb0
   2b7b4:	f90043e0 	str	x0, [sp, #128]
   2b7b8:	1400000d 	b	2b7ec <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1dcc>
   2b7bc:	f94043e1 	ldr	x1, [sp, #128]
   2b7c0:	d2800002 	mov	x2, #0x0                   	// #0
   2b7c4:	f947de60 	ldr	x0, [x19, #4024]
   2b7c8:	97ff66ca 	bl	52f0 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2b7cc:	f947de60 	ldr	x0, [x19, #4024]
   2b7d0:	2a1c03e1 	mov	w1, w28
   2b7d4:	97ff67bf 	bl	56d0 <std::ostream::operator<<(int)@plt>
   2b7d8:	b9409fe0 	ldr	w0, [sp, #156]
   2b7dc:	11000694 	add	w20, w20, #0x1
   2b7e0:	910322b5 	add	x21, x21, #0xc8
   2b7e4:	6b14001f 	cmp	w0, w20
   2b7e8:	54ff980d 	b.le	2aae8 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x10c8>
   2b7ec:	b94002bc 	ldr	w28, [x21]
   2b7f0:	34fffe74 	cbz	w20, 2b7bc <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1d9c>
   2b7f4:	d2800022 	mov	x2, #0x1                   	// #1
   2b7f8:	aa1703e1 	mov	x1, x23
   2b7fc:	17fffff2 	b	2b7c4 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1da4>
   2b800:	b0000160 	adrp	x0, 58000 <typeinfo name for lqcd::Error+0x88>
   2b804:	91030375 	add	x21, x27, #0xc0
   2b808:	52800014 	mov	w20, #0x0                   	// #0
   2b80c:	9132c000 	add	x0, x0, #0xcb0
   2b810:	f90043e0 	str	x0, [sp, #128]
   2b814:	1400000d 	b	2b848 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1e28>
   2b818:	f94043e1 	ldr	x1, [sp, #128]
   2b81c:	d2800002 	mov	x2, #0x0                   	// #0
   2b820:	f947de60 	ldr	x0, [x19, #4024]
   2b824:	97ff66b3 	bl	52f0 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2b828:	f947de60 	ldr	x0, [x19, #4024]
   2b82c:	2a1c03e1 	mov	w1, w28
   2b830:	97ff67a8 	bl	56d0 <std::ostream::operator<<(int)@plt>
   2b834:	b9409fe0 	ldr	w0, [sp, #156]
   2b838:	11000694 	add	w20, w20, #0x1
   2b83c:	910322b5 	add	x21, x21, #0xc8
   2b840:	6b14001f 	cmp	w0, w20
   2b844:	54ff952d 	b.le	2aae8 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x10c8>
   2b848:	b94002bc 	ldr	w28, [x21]
   2b84c:	34fffe74 	cbz	w20, 2b818 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1df8>
   2b850:	d2800022 	mov	x2, #0x1                   	// #1
   2b854:	aa1703e1 	mov	x1, x23
   2b858:	17fffff2 	b	2b820 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1e00>
   2b85c:	f9426765 	ldr	x5, [x27, #1224]
   2b860:	f9426b62 	ldr	x2, [x27, #1232]
   2b864:	d2835004 	mov	x4, #0x1a80                	// #6784
   2b868:	91132360 	add	x0, x27, #0x4c8
   2b86c:	f2a000c4 	movk	x4, #0x6, lsl #16
   2b870:	f900c3e0 	str	x0, [sp, #384]
   2b874:	b0ffffc0 	adrp	x0, 24000 <(anonymous namespace)::coarse_gcr_fused_step(std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, double&) [clone ._omp_fn.1]+0x1a0>
   2b878:	52800003 	mov	w3, #0x0                   	// #0
   2b87c:	91280000 	add	x0, x0, #0xa00
   2b880:	aa1c03e1 	mov	x1, x28
   2b884:	f900c7ff 	str	xzr, [sp, #392]
   2b888:	cb050042 	sub	x2, x2, x5
   2b88c:	eb04005f 	cmp	x2, x4
   2b890:	1a9f87e2 	cset	w2, ls  // ls = plast
   2b894:	97ff672f 	bl	5550 <GOMP_parallel@plt>
   2b898:	fd40c7e0 	ldr	d0, [sp, #392]
   2b89c:	f94057e0 	ldr	x0, [sp, #168]
   2b8a0:	fd001800 	str	d0, [x0, #48]
   2b8a4:	17fff959 	b	29e08 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x3e8>
   2b8a8:	f94063e0 	ldr	x0, [sp, #192]
   2b8ac:	911ce362 	add	x2, x27, #0x738
   2b8b0:	f9400003 	ldr	x3, [x0]
   2b8b4:	f9405be0 	ldr	x0, [sp, #176]
   2b8b8:	f9400001 	ldr	x1, [x0]
   2b8bc:	f94047e0 	ldr	x0, [sp, #136]
   2b8c0:	91036063 	add	x3, x3, #0xd8
   2b8c4:	91036021 	add	x1, x1, #0xd8
   2b8c8:	97fff26e 	bl	28280 <NativeMG::Impl::coarse_reconstruct(std::vector<float, lqcd_native::WorkspaceAllocator<float> > const&, std::vector<float, lqcd_native::WorkspaceAllocator<float> > const&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&) const>
   2b8cc:	17fffbfe 	b	2a8c4 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xea4>
   2b8d0:	f94063e0 	ldr	x0, [sp, #192]
   2b8d4:	9119c362 	add	x2, x27, #0x670
   2b8d8:	f9400003 	ldr	x3, [x0]
   2b8dc:	f9405be0 	ldr	x0, [sp, #176]
   2b8e0:	f9400001 	ldr	x1, [x0]
   2b8e4:	f94047e0 	ldr	x0, [sp, #136]
   2b8e8:	91030063 	add	x3, x3, #0xc0
   2b8ec:	91030021 	add	x1, x1, #0xc0
   2b8f0:	97fff264 	bl	28280 <NativeMG::Impl::coarse_reconstruct(std::vector<float, lqcd_native::WorkspaceAllocator<float> > const&, std::vector<float, lqcd_native::WorkspaceAllocator<float> > const&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&) const>
   2b8f4:	17fffbee 	b	2a8ac <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xe8c>
   2b8f8:	f94063e0 	ldr	x0, [sp, #192]
   2b8fc:	9116a362 	add	x2, x27, #0x5a8
   2b900:	f9400003 	ldr	x3, [x0]
   2b904:	f9405be0 	ldr	x0, [sp, #176]
   2b908:	f9400001 	ldr	x1, [x0]
   2b90c:	f94047e0 	ldr	x0, [sp, #136]
   2b910:	9102a063 	add	x3, x3, #0xa8
   2b914:	9102a021 	add	x1, x1, #0xa8
   2b918:	97fff25a 	bl	28280 <NativeMG::Impl::coarse_reconstruct(std::vector<float, lqcd_native::WorkspaceAllocator<float> > const&, std::vector<float, lqcd_native::WorkspaceAllocator<float> > const&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&) const>
   2b91c:	17fffbde 	b	2a894 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xe74>
   2b920:	f9439365 	ldr	x5, [x27, #1824]
   2b924:	f9439762 	ldr	x2, [x27, #1832]
   2b928:	d2835004 	mov	x4, #0x1a80                	// #6784
   2b92c:	911c8360 	add	x0, x27, #0x720
   2b930:	f2a000c4 	movk	x4, #0x6, lsl #16
   2b934:	f900c3e0 	str	x0, [sp, #384]
   2b938:	b0ffffc0 	adrp	x0, 24000 <(anonymous namespace)::coarse_gcr_fused_step(std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, double&) [clone ._omp_fn.1]+0x1a0>
   2b93c:	52800003 	mov	w3, #0x0                   	// #0
   2b940:	91280000 	add	x0, x0, #0xa00
   2b944:	aa1c03e1 	mov	x1, x28
   2b948:	f900c7ff 	str	xzr, [sp, #392]
   2b94c:	cb050042 	sub	x2, x2, x5
   2b950:	eb04005f 	cmp	x2, x4
   2b954:	1a9f87e2 	cset	w2, ls  // ls = plast
   2b958:	97ff66fe 	bl	5550 <GOMP_parallel@plt>
   2b95c:	fd40c7e0 	ldr	d0, [sp, #392]
   2b960:	f94057e0 	ldr	x0, [sp, #168]
   2b964:	fd002400 	str	d0, [x0, #72]
   2b968:	17fff937 	b	29e44 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x424>
   2b96c:	f9432f65 	ldr	x5, [x27, #1624]
   2b970:	f9433362 	ldr	x2, [x27, #1632]
   2b974:	d2835004 	mov	x4, #0x1a80                	// #6784
   2b978:	91196360 	add	x0, x27, #0x658
   2b97c:	f2a000c4 	movk	x4, #0x6, lsl #16
   2b980:	f900c3e0 	str	x0, [sp, #384]
   2b984:	b0ffffc0 	adrp	x0, 24000 <(anonymous namespace)::coarse_gcr_fused_step(std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, double&) [clone ._omp_fn.1]+0x1a0>
   2b988:	52800003 	mov	w3, #0x0                   	// #0
   2b98c:	91280000 	add	x0, x0, #0xa00
   2b990:	aa1c03e1 	mov	x1, x28
   2b994:	f900c7ff 	str	xzr, [sp, #392]
   2b998:	cb050042 	sub	x2, x2, x5
   2b99c:	eb04005f 	cmp	x2, x4
   2b9a0:	1a9f87e2 	cset	w2, ls  // ls = plast
   2b9a4:	97ff66eb 	bl	5550 <GOMP_parallel@plt>
   2b9a8:	fd40c7e0 	ldr	d0, [sp, #392]
   2b9ac:	f94057e0 	ldr	x0, [sp, #168]
   2b9b0:	fd002000 	str	d0, [x0, #64]
   2b9b4:	17fff91f 	b	29e30 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x410>
   2b9b8:	f942cb65 	ldr	x5, [x27, #1424]
   2b9bc:	f942cf62 	ldr	x2, [x27, #1432]
   2b9c0:	d2835004 	mov	x4, #0x1a80                	// #6784
   2b9c4:	91164360 	add	x0, x27, #0x590
   2b9c8:	f2a000c4 	movk	x4, #0x6, lsl #16
   2b9cc:	f900c3e0 	str	x0, [sp, #384]
   2b9d0:	b0ffffc0 	adrp	x0, 24000 <(anonymous namespace)::coarse_gcr_fused_step(std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, double&) [clone ._omp_fn.1]+0x1a0>
   2b9d4:	52800003 	mov	w3, #0x0                   	// #0
   2b9d8:	91280000 	add	x0, x0, #0xa00
   2b9dc:	aa1c03e1 	mov	x1, x28
   2b9e0:	f900c7ff 	str	xzr, [sp, #392]
   2b9e4:	cb050042 	sub	x2, x2, x5
   2b9e8:	eb04005f 	cmp	x2, x4
   2b9ec:	1a9f87e2 	cset	w2, ls  // ls = plast
   2b9f0:	97ff66d8 	bl	5550 <GOMP_parallel@plt>
   2b9f4:	fd40c7e0 	ldr	d0, [sp, #392]
   2b9f8:	f94057e0 	ldr	x0, [sp, #168]
   2b9fc:	fd001c00 	str	d0, [x0, #56]
   2ba00:	17fff907 	b	29e1c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x3fc>
   2ba04:	f94063e0 	ldr	x0, [sp, #192]
   2ba08:	91138362 	add	x2, x27, #0x4e0
   2ba0c:	f9400003 	ldr	x3, [x0]
   2ba10:	f9405be0 	ldr	x0, [sp, #176]
   2ba14:	f9400001 	ldr	x1, [x0]
   2ba18:	f94047e0 	ldr	x0, [sp, #136]
   2ba1c:	91024063 	add	x3, x3, #0x90
   2ba20:	91024021 	add	x1, x1, #0x90
   2ba24:	97fff217 	bl	28280 <NativeMG::Impl::coarse_reconstruct(std::vector<float, lqcd_native::WorkspaceAllocator<float> > const&, std::vector<float, lqcd_native::WorkspaceAllocator<float> > const&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&) const>
   2ba28:	17fffb95 	b	2a87c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xe5c>
   2ba2c:	9132c000 	add	x0, x0, #0xcb0
   2ba30:	9102e378 	add	x24, x27, #0xb8
   2ba34:	52800016 	mov	w22, #0x0                   	// #0
   2ba38:	f90043e0 	str	x0, [sp, #128]
   2ba3c:	1400000d 	b	2ba70 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x2050>
   2ba40:	d2800022 	mov	x2, #0x1                   	// #1
   2ba44:	aa1503e1 	mov	x1, x21
   2ba48:	f947de60 	ldr	x0, [x19, #4024]
   2ba4c:	97ff6629 	bl	52f0 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2ba50:	f947de60 	ldr	x0, [x19, #4024]
   2ba54:	2a1c03e1 	mov	w1, w28
   2ba58:	97ff671e 	bl	56d0 <std::ostream::operator<<(int)@plt>
   2ba5c:	b9409fe0 	ldr	w0, [sp, #156]
   2ba60:	110006d6 	add	w22, w22, #0x1
   2ba64:	91032318 	add	x24, x24, #0xc8
   2ba68:	6b16001f 	cmp	w0, w22
   2ba6c:	54ffd1ed 	b.le	2b4a8 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1a88>
   2ba70:	b940031c 	ldr	w28, [x24]
   2ba74:	35fffe76 	cbnz	w22, 2ba40 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x2020>
   2ba78:	d2800002 	mov	x2, #0x0                   	// #0
   2ba7c:	f94043e1 	ldr	x1, [sp, #128]
   2ba80:	17fffff2 	b	2ba48 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x2028>
   2ba84:	f947de61 	ldr	x1, [x19, #4024]
   2ba88:	f9400020 	ldr	x0, [x1]
   2ba8c:	f85e8000 	ldur	x0, [x0, #-24]
   2ba90:	8b010000 	add	x0, x0, x1
   2ba94:	b9402001 	ldr	w1, [x0, #32]
   2ba98:	32000021 	orr	w1, w1, #0x1
   2ba9c:	97ff6701 	bl	56a0 <std::basic_ios<char, std::char_traits<char> >::clear(std::_Ios_Iostate)@plt>
   2baa0:	17fffe5f 	b	2b41c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x19fc>
   2baa4:	f943f765 	ldr	x5, [x27, #2024]
   2baa8:	f943fb62 	ldr	x2, [x27, #2032]
   2baac:	d2835004 	mov	x4, #0x1a80                	// #6784
   2bab0:	911fa360 	add	x0, x27, #0x7e8
   2bab4:	f2a000c4 	movk	x4, #0x6, lsl #16
   2bab8:	f900c3e0 	str	x0, [sp, #384]
   2babc:	b0ffffc0 	adrp	x0, 24000 <(anonymous namespace)::coarse_gcr_fused_step(std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, double&) [clone ._omp_fn.1]+0x1a0>
   2bac0:	52800003 	mov	w3, #0x0                   	// #0
   2bac4:	91280000 	add	x0, x0, #0xa00
   2bac8:	aa1c03e1 	mov	x1, x28
   2bacc:	f900c7ff 	str	xzr, [sp, #392]
   2bad0:	cb050042 	sub	x2, x2, x5
   2bad4:	eb04005f 	cmp	x2, x4
   2bad8:	1a9f87e2 	cset	w2, ls  // ls = plast
   2badc:	97ff669d 	bl	5550 <GOMP_parallel@plt>
   2bae0:	fd40c7e0 	ldr	d0, [sp, #392]
   2bae4:	f94057e0 	ldr	x0, [sp, #168]
   2bae8:	fd002800 	str	d0, [x0, #80]
   2baec:	17fff8db 	b	29e58 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x438>
   2baf0:	9132c000 	add	x0, x0, #0xcb0
   2baf4:	9102f378 	add	x24, x27, #0xbc
   2baf8:	52800016 	mov	w22, #0x0                   	// #0
   2bafc:	f90043e0 	str	x0, [sp, #128]
   2bb00:	1400000d 	b	2bb34 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x2114>
   2bb04:	f94043e1 	ldr	x1, [sp, #128]
   2bb08:	d2800002 	mov	x2, #0x0                   	// #0
   2bb0c:	f947de60 	ldr	x0, [x19, #4024]
   2bb10:	97ff65f8 	bl	52f0 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2bb14:	f947de60 	ldr	x0, [x19, #4024]
   2bb18:	2a1c03e1 	mov	w1, w28
   2bb1c:	97ff66ed 	bl	56d0 <std::ostream::operator<<(int)@plt>
   2bb20:	b9409fe0 	ldr	w0, [sp, #156]
   2bb24:	110006d6 	add	w22, w22, #0x1
   2bb28:	91032318 	add	x24, x24, #0xc8
   2bb2c:	6b16001f 	cmp	w0, w22
   2bb30:	54ffcbcd 	b.le	2b4a8 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1a88>
   2bb34:	b940031c 	ldr	w28, [x24]
   2bb38:	34fffe76 	cbz	w22, 2bb04 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x20e4>
   2bb3c:	d2800022 	mov	x2, #0x1                   	// #1
   2bb40:	aa1503e1 	mov	x1, x21
   2bb44:	17fffff2 	b	2bb0c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x20ec>
   2bb48:	aa1403e0 	mov	x0, x20
   2bb4c:	97ff65ed 	bl	5300 <std::ctype<char>::_M_widen_init() const@plt>
   2bb50:	f9400282 	ldr	x2, [x20]
   2bb54:	90000000 	adrp	x0, 2b000 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x15e0>
   2bb58:	52800141 	mov	w1, #0xa                   	// #10
   2bb5c:	91384000 	add	x0, x0, #0xe10
   2bb60:	f9401842 	ldr	x2, [x2, #48]
   2bb64:	eb00005f 	cmp	x2, x0
   2bb68:	54ffcd20 	b.eq	2b50c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1aec>  // b.none
   2bb6c:	aa1403e0 	mov	x0, x20
   2bb70:	d63f0040 	blr	x2
   2bb74:	12001c01 	and	w1, w0, #0xff
   2bb78:	17fffe65 	b	2b50c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1aec>
   2bb7c:	9132c000 	add	x0, x0, #0xcb0
   2bb80:	91030378 	add	x24, x27, #0xc0
   2bb84:	52800016 	mov	w22, #0x0                   	// #0
   2bb88:	f90043e0 	str	x0, [sp, #128]
   2bb8c:	1400000d 	b	2bbc0 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x21a0>
   2bb90:	f94043e1 	ldr	x1, [sp, #128]
   2bb94:	d2800002 	mov	x2, #0x0                   	// #0
   2bb98:	f947de60 	ldr	x0, [x19, #4024]
   2bb9c:	97ff65d5 	bl	52f0 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2bba0:	f947de60 	ldr	x0, [x19, #4024]
   2bba4:	2a1c03e1 	mov	w1, w28
   2bba8:	97ff66ca 	bl	56d0 <std::ostream::operator<<(int)@plt>
   2bbac:	b9409fe0 	ldr	w0, [sp, #156]
   2bbb0:	110006d6 	add	w22, w22, #0x1
   2bbb4:	91032318 	add	x24, x24, #0xc8
   2bbb8:	6b16001f 	cmp	w0, w22
   2bbbc:	54ffc76d 	b.le	2b4a8 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1a88>
   2bbc0:	b940031c 	ldr	w28, [x24]
   2bbc4:	34fffe76 	cbz	w22, 2bb90 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x2170>
   2bbc8:	d2800022 	mov	x2, #0x1                   	// #1
   2bbcc:	aa1503e1 	mov	x1, x21
   2bbd0:	17fffff2 	b	2bb98 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x2178>
   2bbd4:	f94063e0 	ldr	x0, [sp, #192]
   2bbd8:	f9400003 	ldr	x3, [x0]
   2bbdc:	f9405be0 	ldr	x0, [sp, #176]
   2bbe0:	f9400001 	ldr	x1, [x0]
   2bbe4:	f94047e0 	ldr	x0, [sp, #136]
   2bbe8:	9103c063 	add	x3, x3, #0xf0
   2bbec:	9103c021 	add	x1, x1, #0xf0
   2bbf0:	97fff1a4 	bl	28280 <NativeMG::Impl::coarse_reconstruct(std::vector<float, lqcd_native::WorkspaceAllocator<float> > const&, std::vector<float, lqcd_native::WorkspaceAllocator<float> > const&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&) const>
   2bbf4:	17fffb3b 	b	2a8e0 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xec0>
   2bbf8:	97ff65ea 	bl	53a0 <std::__throw_bad_cast()@plt>
   2bbfc:	97ff65e9 	bl	53a0 <std::__throw_bad_cast()@plt>
   2bc00:	1e61c000 	fsqrt	d0, d0
   2bc04:	17fffa3c 	b	2a4f4 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xad4>
   2bc08:	d2800200 	mov	x0, #0x10                  	// #16
   2bc0c:	97ff6509 	bl	5030 <__cxa_allocate_exception@plt>
   2bc10:	aa0003f3 	mov	x19, x0
   2bc14:	b0000161 	adrp	x1, 58000 <typeinfo name for lqcd::Error+0x88>
   2bc18:	91254021 	add	x1, x1, #0x950
   2bc1c:	97ff64ed 	bl	4fd0 <std::runtime_error::runtime_error(char const*)@plt>
   2bc20:	900002a2 	adrp	x2, 7f000 <__FRAME_END__+0x1ea64>
   2bc24:	900002a1 	adrp	x1, 7f000 <__FRAME_END__+0x1ea64>
   2bc28:	aa1303e0 	mov	x0, x19
   2bc2c:	a9025bf5 	stp	x21, x22, [sp, #32]
   2bc30:	f9479c42 	ldr	x2, [x2, #3896]
   2bc34:	f947e421 	ldr	x1, [x1, #4040]
   2bc38:	6d0627e8 	stp	d8, d9, [sp, #96]
   2bc3c:	a90363f7 	stp	x23, x24, [sp, #48]
   2bc40:	a9046bf9 	stp	x25, x26, [sp, #64]
   2bc44:	a90573fb 	stp	x27, x28, [sp, #80]
   2bc48:	97ff669a 	bl	56b0 <__cxa_throw@plt>
   2bc4c:	aa0003f3 	mov	x19, x0
   2bc50:	b94127e0 	ldr	w0, [sp, #292]
   2bc54:	97ff659b 	bl	52c0 <omp_set_num_threads@plt>
   2bc58:	aa1303e0 	mov	x0, x19
   2bc5c:	a90363f7 	stp	x23, x24, [sp, #48]
   2bc60:	a9046bf9 	stp	x25, x26, [sp, #64]
   2bc64:	6d0627e8 	stp	d8, d9, [sp, #96]
   2bc68:	97ff66a6 	bl	5700 <_Unwind_Resume@plt>
   2bc6c:	aa0003e1 	mov	x1, x0
   2bc70:	aa1303e0 	mov	x0, x19
   2bc74:	a9025bf5 	stp	x21, x22, [sp, #32]
   2bc78:	a90363f7 	stp	x23, x24, [sp, #48]
   2bc7c:	aa0103f3 	mov	x19, x1
   2bc80:	a9046bf9 	stp	x25, x26, [sp, #64]
   2bc84:	a90573fb 	stp	x27, x28, [sp, #80]
   2bc88:	6d0627e8 	stp	d8, d9, [sp, #96]
   2bc8c:	97ff6541 	bl	5190 <__cxa_free_exception@plt>
   2bc90:	aa1303e0 	mov	x0, x19
   2bc94:	97ff669b 	bl	5700 <_Unwind_Resume@plt>
   2bc98:	aa0003f3 	mov	x19, x0
   2bc9c:	f94057e0 	ldr	x0, [sp, #168]
   2bca0:	f94073e1 	ldr	x1, [sp, #224]
   2bca4:	aa1b03f4 	mov	x20, x27
   2bca8:	97ff656a 	bl	5250 <operator delete(void*, unsigned long)@plt>
   2bcac:	a94363f7 	ldp	x23, x24, [sp, #48]
   2bcb0:	a9446bf9 	ldp	x25, x26, [sp, #64]
   2bcb4:	6d4627e8 	ldp	d8, d9, [sp, #96]
   2bcb8:	f94077e0 	ldr	x0, [sp, #232]
   2bcbc:	eb00029f 	cmp	x20, x0
   2bcc0:	540004e1 	b.ne	2bd5c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x233c>  // b.any
   2bcc4:	f94083e1 	ldr	x1, [sp, #256]
   2bcc8:	aa1b03e0 	mov	x0, x27
   2bccc:	97ff6561 	bl	5250 <operator delete(void*, unsigned long)@plt>
   2bcd0:	b94123e0 	ldr	w0, [sp, #288]
   2bcd4:	34fffc20 	cbz	w0, 2bc58 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x2238>
   2bcd8:	17ffffde 	b	2bc50 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x2230>
   2bcdc:	aa1b03f4 	mov	x20, x27
   2bce0:	aa0003f3 	mov	x19, x0
   2bce4:	17fffff5 	b	2bcb8 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x2298>
   2bce8:	f940c3e1 	ldr	x1, [sp, #384]
   2bcec:	aa0003f3 	mov	x19, x0
   2bcf0:	b5000281 	cbnz	x1, 2bd40 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x2320>
   2bcf4:	f94067e0 	ldr	x0, [sp, #200]
   2bcf8:	f9407be1 	ldr	x1, [sp, #240]
   2bcfc:	97ff6555 	bl	5250 <operator delete(void*, unsigned long)@plt>
   2bd00:	f9405fe1 	ldr	x1, [sp, #184]
   2bd04:	aa1a03e0 	mov	x0, x26
   2bd08:	97ff6552 	bl	5250 <operator delete(void*, unsigned long)@plt>
   2bd0c:	f940b7e0 	ldr	x0, [sp, #360]
   2bd10:	f940bfe1 	ldr	x1, [sp, #376]
   2bd14:	cb000021 	sub	x1, x1, x0
   2bd18:	b4000040 	cbz	x0, 2bd20 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x2300>
   2bd1c:	97ff654d 	bl	5250 <operator delete(void*, unsigned long)@plt>
   2bd20:	f940abe0 	ldr	x0, [sp, #336]
   2bd24:	f940b3e1 	ldr	x1, [sp, #352]
   2bd28:	cb000021 	sub	x1, x1, x0
   2bd2c:	b4fffb80 	cbz	x0, 2bc9c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x227c>
   2bd30:	97ff6548 	bl	5250 <operator delete(void*, unsigned long)@plt>
   2bd34:	17ffffda 	b	2bc9c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x227c>
   2bd38:	aa0003f3 	mov	x19, x0
   2bd3c:	17ffffee 	b	2bcf4 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x22d4>
   2bd40:	aa0103e0 	mov	x0, x1
   2bd44:	97ff64cf 	bl	5080 <free@plt>
   2bd48:	17ffffeb 	b	2bcf4 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x22d4>
   2bd4c:	aa0003f3 	mov	x19, x0
   2bd50:	17ffffec 	b	2bd00 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x22e0>
   2bd54:	aa0003f3 	mov	x19, x0
   2bd58:	17ffffed 	b	2bd0c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x22ec>
   2bd5c:	a9495a95 	ldp	x21, x22, [x20, #144]
   2bd60:	eb1502df 	cmp	x22, x21
   2bd64:	540003e1 	b.ne	2bde0 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x23c0>  // b.any
   2bd68:	f9404a80 	ldr	x0, [x20, #144]
   2bd6c:	f9405281 	ldr	x1, [x20, #160]
   2bd70:	cb000021 	sub	x1, x1, x0
   2bd74:	b4000040 	cbz	x0, 2bd7c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x235c>
   2bd78:	97ff6536 	bl	5250 <operator delete(void*, unsigned long)@plt>
   2bd7c:	a947da95 	ldp	x21, x22, [x20, #120]
   2bd80:	eb1502df 	cmp	x22, x21
   2bd84:	54000381 	b.ne	2bdf4 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x23d4>  // b.any
   2bd88:	f9403e80 	ldr	x0, [x20, #120]
   2bd8c:	f9404681 	ldr	x1, [x20, #136]
   2bd90:	cb000021 	sub	x1, x1, x0
   2bd94:	b4000040 	cbz	x0, 2bd9c <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x237c>
   2bd98:	97ff652e 	bl	5250 <operator delete(void*, unsigned long)@plt>
   2bd9c:	f9403280 	ldr	x0, [x20, #96]
   2bda0:	b4000040 	cbz	x0, 2bda8 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x2388>
   2bda4:	97ff64b7 	bl	5080 <free@plt>
   2bda8:	f9402680 	ldr	x0, [x20, #72]
   2bdac:	b4000040 	cbz	x0, 2bdb4 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x2394>
   2bdb0:	97ff64b4 	bl	5080 <free@plt>
   2bdb4:	f9401a80 	ldr	x0, [x20, #48]
   2bdb8:	b4000040 	cbz	x0, 2bdc0 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x23a0>
   2bdbc:	97ff64b1 	bl	5080 <free@plt>
   2bdc0:	f9400e80 	ldr	x0, [x20, #24]
   2bdc4:	b4000040 	cbz	x0, 2bdcc <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x23ac>
   2bdc8:	97ff64ae 	bl	5080 <free@plt>
   2bdcc:	f9400280 	ldr	x0, [x20]
   2bdd0:	b4000040 	cbz	x0, 2bdd8 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x23b8>
   2bdd4:	97ff64ab 	bl	5080 <free@plt>
   2bdd8:	91032294 	add	x20, x20, #0xc8
   2bddc:	17ffffb7 	b	2bcb8 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x2298>
   2bde0:	f94002a0 	ldr	x0, [x21]
   2bde4:	b4000040 	cbz	x0, 2bdec <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x23cc>
   2bde8:	97ff64a6 	bl	5080 <free@plt>
   2bdec:	910062b5 	add	x21, x21, #0x18
   2bdf0:	17ffffdc 	b	2bd60 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x2340>
   2bdf4:	f94002a0 	ldr	x0, [x21]
   2bdf8:	b4000040 	cbz	x0, 2be00 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x23e0>
   2bdfc:	97ff64a1 	bl	5080 <free@plt>
   2be00:	910062b5 	add	x21, x21, #0x18
   2be04:	17ffffdf 	b	2bd80 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x2360>
