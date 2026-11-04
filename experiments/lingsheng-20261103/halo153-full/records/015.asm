
/home/share/nsls_lwb/.cache/mg-opt-20261103/campaign-halo-v2/attempts/000-halo-v2-tests/build/liblqcd_cpu.so.0.2.0:     file format elf64-littleaarch64


Disassembly of section .text:

000000000002b1c0 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const>:
   2b1c0:	a9a17bfd 	stp	x29, x30, [sp, #-496]!
   2b1c4:	910003fd 	mov	x29, sp
   2b1c8:	f9005fe1 	str	x1, [sp, #184]
   2b1cc:	395ec801 	ldrb	w1, [x0, #1970]
   2b1d0:	6d0627e8 	stp	d8, d9, [sp, #96]
   2b1d4:	a9025bf5 	stp	x21, x22, [sp, #32]
   2b1d8:	a90363f7 	stp	x23, x24, [sp, #48]
   2b1dc:	a9046bf9 	stp	x25, x26, [sp, #64]
   2b1e0:	a90573fb 	stp	x27, x28, [sp, #80]
   2b1e4:	aa0003fc 	mov	x28, x0
   2b1e8:	fd003bea 	str	d10, [sp, #112]
   2b1ec:	b90097e3 	str	w3, [sp, #148]
   2b1f0:	f9006fe2 	str	x2, [sp, #216]
   2b1f4:	340000e1 	cbz	w1, 2b210 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x50>
   2b1f8:	7100047f 	cmp	w3, #0x1
   2b1fc:	54001d20 	b.eq	2b5a0 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x3e0>  // b.none
   2b200:	39590400 	ldrb	w0, [x0, #1601]
   2b204:	34000060 	cbz	w0, 2b210 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x50>
   2b208:	3968ff95 	ldrb	w21, [x28, #2623]
   2b20c:	34000395 	cbz	w21, 2b27c <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xbc>
   2b210:	b94097f7 	ldr	w23, [sp, #148]
   2b214:	710002ff 	cmp	w23, #0x0
   2b218:	5400022d 	b.le	2b25c <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x9c>
   2b21c:	f9405ff5 	ldr	x21, [sp, #184]
   2b220:	f9406ff6 	ldr	x22, [sp, #216]
   2b224:	a90153f3 	stp	x19, x20, [sp, #16]
   2b228:	d2800013 	mov	x19, #0x0                   	// #0
   2b22c:	52800014 	mov	w20, #0x0                   	// #0
   2b230:	f94002a1 	ldr	x1, [x21]
   2b234:	f94002c2 	ldr	x2, [x22]
   2b238:	aa1c03e0 	mov	x0, x28
   2b23c:	11000694 	add	w20, w20, #0x1
   2b240:	8b130021 	add	x1, x1, x19
   2b244:	8b130042 	add	x2, x2, x19
   2b248:	91006273 	add	x19, x19, #0x18
   2b24c:	97fff7bd 	bl	29140 <NativeMG::Impl::coarse_solve(std::vector<float, lqcd_native::WorkspaceAllocator<float> > const&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&) const>
   2b250:	6b17029f 	cmp	w20, w23
   2b254:	54fffeeb 	b.lt	2b230 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x70>  // b.tstop
   2b258:	a94153f3 	ldp	x19, x20, [sp, #16]
   2b25c:	a9425bf5 	ldp	x21, x22, [sp, #32]
   2b260:	a94363f7 	ldp	x23, x24, [sp, #48]
   2b264:	a9446bf9 	ldp	x25, x26, [sp, #64]
   2b268:	a94573fb 	ldp	x27, x28, [sp, #80]
   2b26c:	6d4627e8 	ldp	d8, d9, [sp, #96]
   2b270:	fd403bea 	ldr	d10, [sp, #112]
   2b274:	a8df7bfd 	ldp	x29, x30, [sp], #496
   2b278:	d65f03c0 	ret
   2b27c:	d0000180 	adrp	x0, 5d000 <_fini+0x34>
   2b280:	52800021 	mov	w1, #0x1                   	// #1
   2b284:	91258000 	add	x0, x0, #0x960
   2b288:	97ff885a 	bl	d3f0 <lqcd_native::detail::setting(char const*, int)>
   2b28c:	34fffc20 	cbz	w0, 2b210 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x50>
   2b290:	a90153f3 	stp	x19, x20, [sp, #16]
   2b294:	b94a4393 	ldr	w19, [x28, #2624]
   2b298:	97ff6902 	bl	56a0 <omp_get_max_threads@plt>
   2b29c:	b90133e0 	str	w0, [sp, #304]
   2b2a0:	7100027f 	cmp	w19, #0x0
   2b2a4:	5400834c 	b.gt	2c30c <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x114c>
   2b2a8:	b90137ff 	str	wzr, [sp, #308]
   2b2ac:	d2947ae0 	mov	x0, #0xa3d7                	// #41943
   2b2b0:	b98097fb 	ldrsw	x27, [sp, #148]
   2b2b4:	f2a7ae00 	movk	x0, #0x3d70, lsl #16
   2b2b8:	f2dae140 	movk	x0, #0xd70a, lsl #32
   2b2bc:	f2e01460 	movk	x0, #0xa3, lsl #48
   2b2c0:	eb00037f 	cmp	x27, x0
   2b2c4:	5400dc68 	b.hi	2ce50 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1c90>  // b.pmore
   2b2c8:	b94097e0 	ldr	w0, [sp, #148]
   2b2cc:	52801913 	mov	w19, #0xc8                  	// #200
   2b2d0:	a9167fff 	stp	xzr, xzr, [sp, #352]
   2b2d4:	f900bbff 	str	xzr, [sp, #368]
   2b2d8:	9b337c13 	smull	x19, w0, w19
   2b2dc:	b400603b 	cbz	x27, 2bee0 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xd20>
   2b2e0:	aa1303e0 	mov	x0, x19
   2b2e4:	97ff67df 	bl	5260 <operator new(unsigned long)@plt>
   2b2e8:	8b130013 	add	x19, x0, x19
   2b2ec:	f900b3e0 	str	x0, [sp, #352]
   2b2f0:	f900bbf3 	str	x19, [sp, #368]
   2b2f4:	d503201f 	nop
   2b2f8:	a9007c1f 	stp	xzr, xzr, [x0]
   2b2fc:	a9017c1f 	stp	xzr, xzr, [x0, #16]
   2b300:	a9027c1f 	stp	xzr, xzr, [x0, #32]
   2b304:	a9037c1f 	stp	xzr, xzr, [x0, #48]
   2b308:	a9047c1f 	stp	xzr, xzr, [x0, #64]
   2b30c:	a9057c1f 	stp	xzr, xzr, [x0, #80]
   2b310:	a9067c1f 	stp	xzr, xzr, [x0, #96]
   2b314:	a9077c1f 	stp	xzr, xzr, [x0, #112]
   2b318:	a9087c1f 	stp	xzr, xzr, [x0, #128]
   2b31c:	a9097c1f 	stp	xzr, xzr, [x0, #144]
   2b320:	91032000 	add	x0, x0, #0xc8
   2b324:	a93dfc1f 	stp	xzr, xzr, [x0, #-40]
   2b328:	a93efc1f 	stp	xzr, xzr, [x0, #-24]
   2b32c:	f81f801f 	stur	xzr, [x0, #-8]
   2b330:	eb00027f 	cmp	x19, x0
   2b334:	54fffe21 	b.ne	2b2f8 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x138>  // b.any
   2b338:	d37df374 	lsl	x20, x27, #3
   2b33c:	aa1403e0 	mov	x0, x20
   2b340:	f900b7f3 	str	x19, [sp, #360]
   2b344:	97ff67c7 	bl	5260 <operator new(unsigned long)@plt>
   2b348:	8b140003 	add	x3, x0, x20
   2b34c:	aa1403e2 	mov	x2, x20
   2b350:	52800001 	mov	w1, #0x0                   	// #0
   2b354:	f90053e0 	str	x0, [sp, #160]
   2b358:	f90087e3 	str	x3, [sp, #264]
   2b35c:	97ff6759 	bl	50c0 <memset@plt>
   2b360:	b94097e0 	ldr	w0, [sp, #148]
   2b364:	7100001f 	cmp	w0, #0x0
   2b368:	5400d62d 	b.le	2ce2c <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1c6c>
   2b36c:	b94097e0 	ldr	w0, [sp, #148]
   2b370:	52800318 	mov	w24, #0x18                  	// #24
   2b374:	f94053f7 	ldr	x23, [sp, #160]
   2b378:	b0ffffd9 	adrp	x25, 24000 <(anonymous namespace)::coarse_gcr_fused_step(std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, double&) [clone ._omp_fn.1]+0x90>
   2b37c:	d283501a 	mov	x26, #0x1a80                	// #6784
   2b380:	0f000408 	movi	v8.2s, #0x0
   2b384:	912c4339 	add	x25, x25, #0xb10
   2b388:	d2800016 	mov	x22, #0x0                   	// #0
   2b38c:	d2800014 	mov	x20, #0x0                   	// #0
   2b390:	9106c3f3 	add	x19, sp, #0x1b0
   2b394:	2f00e409 	movi	d9, #0x0
   2b398:	f2a000da 	movk	x26, #0x6, lsl #16
   2b39c:	9b387c18 	smull	x24, w0, w24
   2b3a0:	f9405fe0 	ldr	x0, [sp, #184]
   2b3a4:	f9406fe2 	ldr	x2, [sp, #216]
   2b3a8:	f9400001 	ldr	x1, [x0]
   2b3ac:	f9400040 	ldr	x0, [x2]
   2b3b0:	aa1303e2 	mov	x2, x19
   2b3b4:	8b140024 	add	x4, x1, x20
   2b3b8:	f8746823 	ldr	x3, [x1, x20]
   2b3bc:	8b140000 	add	x0, x0, x20
   2b3c0:	f9400481 	ldr	x1, [x4, #8]
   2b3c4:	bd01b3e8 	str	s8, [sp, #432]
   2b3c8:	cb030021 	sub	x1, x1, x3
   2b3cc:	9342fc21 	asr	x1, x1, #2
   2b3d0:	97fffbdc 	bl	2a340 <std::vector<float, lqcd_native::WorkspaceAllocator<float> >::_M_fill_assign(unsigned long, float const&)>
   2b3d4:	f9405fe0 	ldr	x0, [sp, #184]
   2b3d8:	aa1303e2 	mov	x2, x19
   2b3dc:	f9400001 	ldr	x1, [x0]
   2b3e0:	f940b3e0 	ldr	x0, [sp, #352]
   2b3e4:	8b140024 	add	x4, x1, x20
   2b3e8:	f8746823 	ldr	x3, [x1, x20]
   2b3ec:	8b160000 	add	x0, x0, x22
   2b3f0:	f9400481 	ldr	x1, [x4, #8]
   2b3f4:	9100c000 	add	x0, x0, #0x30
   2b3f8:	bd01b3e8 	str	s8, [sp, #432]
   2b3fc:	cb030021 	sub	x1, x1, x3
   2b400:	9342fc21 	asr	x1, x1, #2
   2b404:	97fffbcf 	bl	2a340 <std::vector<float, lqcd_native::WorkspaceAllocator<float> >::_M_fill_assign(unsigned long, float const&)>
   2b408:	f9405fe0 	ldr	x0, [sp, #184]
   2b40c:	52800003 	mov	w3, #0x0                   	// #0
   2b410:	aa1303e1 	mov	x1, x19
   2b414:	910322d6 	add	x22, x22, #0xc8
   2b418:	f9400002 	ldr	x2, [x0]
   2b41c:	aa1903e0 	mov	x0, x25
   2b420:	8b140044 	add	x4, x2, x20
   2b424:	f8746845 	ldr	x5, [x2, x20]
   2b428:	91006294 	add	x20, x20, #0x18
   2b42c:	f9400482 	ldr	x2, [x4, #8]
   2b430:	f900dbe4 	str	x4, [sp, #432]
   2b434:	fd00dfe9 	str	d9, [sp, #440]
   2b438:	cb050042 	sub	x2, x2, x5
   2b43c:	eb1a005f 	cmp	x2, x26
   2b440:	1a9f87e2 	cset	w2, ls  // ls = plast
   2b444:	97ff684b 	bl	5570 <GOMP_parallel@plt>
   2b448:	fd40dfe0 	ldr	d0, [sp, #440]
   2b44c:	fc0086e0 	str	d0, [x23], #8
   2b450:	eb14031f 	cmp	x24, x20
   2b454:	54fffa61 	b.ne	2b3a0 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1e0>  // b.any
   2b458:	900002a0 	adrp	x0, 7f000 <__FRAME_END__+0x18c0c>
   2b45c:	f90057e0 	str	x0, [sp, #168]
   2b460:	f9475800 	ldr	x0, [x0, #3760]
   2b464:	b9400000 	ldr	w0, [x0]
   2b468:	7100041f 	cmp	w0, #0x1
   2b46c:	f94087e0 	ldr	x0, [sp, #264]
   2b470:	f9007be0 	str	x0, [sp, #240]
   2b474:	540054ec 	b.gt	2bf10 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xd50>
   2b478:	d2800013 	mov	x19, #0x0                   	// #0
   2b47c:	d2801916 	mov	x22, #0xc8                  	// #200
   2b480:	f94053e0 	ldr	x0, [sp, #160]
   2b484:	f940b3f4 	ldr	x20, [sp, #352]
   2b488:	fc737800 	ldr	d0, [x0, x19, lsl #3]
   2b48c:	9b165274 	madd	x20, x19, x22, x20
   2b490:	1e602008 	fcmp	d0, #0.0
   2b494:	54000065 	b.pl	2b4a0 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x2e0>  // b.nfrst
   2b498:	97ff68da 	bl	5800 <sqrt@plt>
   2b49c:	14000002 	b	2b4a4 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x2e4>
   2b4a0:	1e61c000 	fsqrt	d0, d0
   2b4a4:	1e602008 	fcmp	d0, #0.0
   2b4a8:	fd005680 	str	d0, [x20, #168]
   2b4ac:	1a9f17e1 	cset	w1, eq  // eq = none
   2b4b0:	1a9f07e0 	cset	w0, ne  // ne = any
   2b4b4:	39031281 	strb	w1, [x20, #196]
   2b4b8:	2a0002b5 	orr	w21, w21, w0
   2b4bc:	54000160 	b.eq	2b4e8 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x328>  // b.none
   2b4c0:	f9405fe0 	ldr	x0, [sp, #184]
   2b4c4:	8b130661 	add	x1, x19, x19, lsl #1
   2b4c8:	aa1403e2 	mov	x2, x20
   2b4cc:	f9400003 	ldr	x3, [x0]
   2b4d0:	aa1c03e0 	mov	x0, x28
   2b4d4:	8b010c61 	add	x1, x3, x1, lsl #3
   2b4d8:	97fff356 	bl	28230 <NativeMG::Impl::coarse_reduced_rhs(std::vector<float, lqcd_native::WorkspaceAllocator<float> > const&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&) const>
   2b4dc:	aa1403e1 	mov	x1, x20
   2b4e0:	91006280 	add	x0, x20, #0x18
   2b4e4:	97ffecf3 	bl	268b0 <std::vector<float, lqcd_native::WorkspaceAllocator<float> >::operator=(std::vector<float, lqcd_native::WorkspaceAllocator<float> > const&) [clone .isra.0]>
   2b4e8:	b94097e0 	ldr	w0, [sp, #148]
   2b4ec:	91000673 	add	x19, x19, #0x1
   2b4f0:	6b13001f 	cmp	w0, w19
   2b4f4:	54fffc6c 	b.gt	2b480 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x2c0>
   2b4f8:	340052b5 	cbz	w21, 2bf4c <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xd8c>
   2b4fc:	f94053e1 	ldr	x1, [sp, #160]
   2b500:	f9407be0 	ldr	x0, [sp, #240]
   2b504:	eb01001f 	cmp	x0, x1
   2b508:	540000c0 	b.eq	2b520 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x360>  // b.none
   2b50c:	aa0003e1 	mov	x1, x0
   2b510:	f94053e0 	ldr	x0, [sp, #160]
   2b514:	cb000022 	sub	x2, x1, x0
   2b518:	52800001 	mov	w1, #0x0                   	// #0
   2b51c:	97ff66e9 	bl	50c0 <memset@plt>
   2b520:	b0ffffd6 	adrp	x22, 24000 <(anonymous namespace)::coarse_gcr_fused_step(std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, double&) [clone ._omp_fn.1]+0x90>
   2b524:	d2835013 	mov	x19, #0x1a80                	// #6784
   2b528:	b94097f9 	ldr	w25, [sp, #148]
   2b52c:	d2800015 	mov	x21, #0x0                   	// #0
   2b530:	d2800014 	mov	x20, #0x0                   	// #0
   2b534:	2f00e408 	movi	d8, #0x0
   2b538:	912c42d6 	add	x22, x22, #0xb10
   2b53c:	f2a000d3 	movk	x19, #0x6, lsl #16
   2b540:	9106c3f7 	add	x23, sp, #0x1b0
   2b544:	f94053f8 	ldr	x24, [sp, #160]
   2b548:	14000005 	b	2b55c <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x39c>
   2b54c:	91000694 	add	x20, x20, #0x1
   2b550:	910322b5 	add	x21, x21, #0xc8
   2b554:	6b14033f 	cmp	w25, w20
   2b558:	540003ad 	b.le	2b5cc <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x40c>
   2b55c:	f940b3e2 	ldr	x2, [sp, #352]
   2b560:	8b150042 	add	x2, x2, x21
   2b564:	39431043 	ldrb	w3, [x2, #196]
   2b568:	35ffff23 	cbnz	w3, 2b54c <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x38c>
   2b56c:	91006044 	add	x4, x2, #0x18
   2b570:	a9418845 	ldp	x5, x2, [x2, #24]
   2b574:	aa1703e1 	mov	x1, x23
   2b578:	aa1603e0 	mov	x0, x22
   2b57c:	f900dbe4 	str	x4, [sp, #432]
   2b580:	fd00dfe8 	str	d8, [sp, #440]
   2b584:	cb050042 	sub	x2, x2, x5
   2b588:	eb13005f 	cmp	x2, x19
   2b58c:	1a9f87e2 	cset	w2, ls  // ls = plast
   2b590:	97ff67f8 	bl	5570 <GOMP_parallel@plt>
   2b594:	fd40dfe0 	ldr	d0, [sp, #440]
   2b598:	fc347b00 	str	d0, [x24, x20, lsl #3]
   2b59c:	17ffffec 	b	2b54c <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x38c>
   2b5a0:	f9405fe1 	ldr	x1, [sp, #184]
   2b5a4:	6d4627e8 	ldp	d8, d9, [sp, #96]
   2b5a8:	fd403bea 	ldr	d10, [sp, #112]
   2b5ac:	f9400042 	ldr	x2, [x2]
   2b5b0:	a9425bf5 	ldp	x21, x22, [sp, #32]
   2b5b4:	a94363f7 	ldp	x23, x24, [sp, #48]
   2b5b8:	a9446bf9 	ldp	x25, x26, [sp, #64]
   2b5bc:	a94573fb 	ldp	x27, x28, [sp, #80]
   2b5c0:	f9400021 	ldr	x1, [x1]
   2b5c4:	a8df7bfd 	ldp	x29, x30, [sp], #496
   2b5c8:	17fff6de 	b	29140 <NativeMG::Impl::coarse_solve(std::vector<float, lqcd_native::WorkspaceAllocator<float> > const&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&) const>
   2b5cc:	f94057e0 	ldr	x0, [sp, #168]
   2b5d0:	f9475800 	ldr	x0, [x0, #3760]
   2b5d4:	b9400000 	ldr	w0, [x0]
   2b5d8:	7100041f 	cmp	w0, #0x1
   2b5dc:	54006b2c 	b.gt	2c340 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1180>
   2b5e0:	b94097f5 	ldr	w21, [sp, #148]
   2b5e4:	d2800014 	mov	x20, #0x0                   	// #0
   2b5e8:	d2800013 	mov	x19, #0x0                   	// #0
   2b5ec:	d503201f 	nop
   2b5f0:	f94053e0 	ldr	x0, [sp, #160]
   2b5f4:	fc737800 	ldr	d0, [x0, x19, lsl #3]
   2b5f8:	1e602008 	fcmp	d0, #0.0
   2b5fc:	540000a5 	b.pl	2b610 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x450>  // b.nfrst
   2b600:	97ff6880 	bl	5800 <sqrt@plt>
   2b604:	91000673 	add	x19, x19, #0x1
   2b608:	f940b3e0 	ldr	x0, [sp, #352]
   2b60c:	14000004 	b	2b61c <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x45c>
   2b610:	1e61c000 	fsqrt	d0, d0
   2b614:	f940b3e0 	ldr	x0, [sp, #352]
   2b618:	91000673 	add	x19, x19, #0x1
   2b61c:	8b140000 	add	x0, x0, x20
   2b620:	91032294 	add	x20, x20, #0xc8
   2b624:	fd005800 	str	d0, [x0, #176]
   2b628:	6b1302bf 	cmp	w21, w19
   2b62c:	54fffe2c 	b.gt	2b5f0 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x430>
   2b630:	9105e3e0 	add	x0, sp, #0x178
   2b634:	aa1b03e1 	mov	x1, x27
   2b638:	a917ffff 	stp	xzr, xzr, [sp, #376]
   2b63c:	a918ffff 	stp	xzr, xzr, [sp, #392]
   2b640:	f9008fe0 	str	x0, [sp, #280]
   2b644:	a919ffff 	stp	xzr, xzr, [sp, #408]
   2b648:	97ff678a 	bl	5470 <std::vector<int, std::allocator<int> >::reserve(unsigned long)@plt>
   2b64c:	910643e0 	add	x0, sp, #0x190
   2b650:	aa1b03e1 	mov	x1, x27
   2b654:	f90097e0 	str	x0, [sp, #296]
   2b658:	97ff6786 	bl	5470 <std::vector<int, std::allocator<int> >::reserve(unsigned long)@plt>
   2b65c:	b94097e0 	ldr	w0, [sp, #148]
   2b660:	92fe0001 	mov	x1, #0xfffffffffffffff     	// #1152921504606846975
   2b664:	531f7813 	lsl	w19, w0, #1
   2b668:	93407e60 	sxtw	x0, w19
   2b66c:	eb01001f 	cmp	x0, x1
   2b670:	5400bd88 	b.hi	2ce20 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1c60>  // b.pmore
   2b674:	d37df014 	lsl	x20, x0, #3
   2b678:	b4006a60 	cbz	x0, 2c3c4 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1204>
   2b67c:	aa1403e0 	mov	x0, x20
   2b680:	97ff66f8 	bl	5260 <operator new(unsigned long)@plt>
   2b684:	8b140003 	add	x3, x0, x20
   2b688:	aa0003fb 	mov	x27, x0
   2b68c:	f9009fe3 	str	x3, [sp, #312]
   2b690:	eb00007f 	cmp	x3, x0
   2b694:	5400bc20 	b.eq	2ce18 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1c58>  // b.none
   2b698:	aa1403e2 	mov	x2, x20
   2b69c:	52800001 	mov	w1, #0x0                   	// #0
   2b6a0:	f9005be3 	str	x3, [sp, #176]
   2b6a4:	97ff6687 	bl	50c0 <memset@plt>
   2b6a8:	b94097e0 	ldr	w0, [sp, #148]
   2b6ac:	92fe0001 	mov	x1, #0xfffffffffffffff     	// #1152921504606846975
   2b6b0:	0b000260 	add	w0, w19, w0
   2b6b4:	93407c00 	sxtw	x0, w0
   2b6b8:	eb01001f 	cmp	x0, x1
   2b6bc:	5400bc08 	b.hi	2ce3c <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1c7c>  // b.pmore
   2b6c0:	d37df013 	lsl	x19, x0, #3
   2b6c4:	b400b400 	cbz	x0, 2cd44 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1b84>
   2b6c8:	aa1303e0 	mov	x0, x19
   2b6cc:	97ff66e5 	bl	5260 <operator new(unsigned long)@plt>
   2b6d0:	8b130002 	add	x2, x0, x19
   2b6d4:	f90063e0 	str	x0, [sp, #192]
   2b6d8:	f90073e2 	str	x2, [sp, #224]
   2b6dc:	eb00005f 	cmp	x2, x0
   2b6e0:	54000080 	b.eq	2b6f0 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x530>  // b.none
   2b6e4:	aa1303e2 	mov	x2, x19
   2b6e8:	52800001 	mov	w1, #0x0                   	// #0
   2b6ec:	97ff6675 	bl	50c0 <memset@plt>
   2b6f0:	b94b6380 	ldr	w0, [x28, #2912]
   2b6f4:	f940b3fa 	ldr	x26, [sp, #352]
   2b6f8:	7100001f 	cmp	w0, #0x0
   2b6fc:	5400b6ed 	b.le	2cdd8 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1c18>
   2b700:	f94063e2 	ldr	x2, [sp, #192]
   2b704:	f94073e1 	ldr	x1, [sp, #224]
   2b708:	f9405be0 	ldr	x0, [sp, #176]
   2b70c:	f94053e3 	ldr	x3, [sp, #160]
   2b710:	cb020021 	sub	x1, x1, x2
   2b714:	f9407be2 	ldr	x2, [sp, #240]
   2b718:	cb1b0000 	sub	x0, x0, x27
   2b71c:	a90c87e0 	stp	x0, x1, [sp, #200]
   2b720:	d3438800 	ubfx	x0, x0, #3, #32
   2b724:	f90077e0 	str	x0, [sp, #232]
   2b728:	d3438820 	ubfx	x0, x1, #3, #32
   2b72c:	f90093e0 	str	x0, [sp, #288]
   2b730:	cb030042 	sub	x2, x2, x3
   2b734:	f0000183 	adrp	x3, 5e000 <typeinfo name for lqcd::Error+0x9b8>
   2b738:	fd40086a 	ldr	d10, [x3, #16]
   2b73c:	52800043 	mov	w3, #0x2                   	// #2
   2b740:	d3438840 	ubfx	x0, x2, #3, #32
   2b744:	f90083e2 	str	x2, [sp, #256]
   2b748:	291f7fe3 	stp	w3, wzr, [sp, #248]
   2b74c:	f9008be0 	str	x0, [sp, #272]
   2b750:	a95783f4 	ldp	x20, x0, [sp, #376]
   2b754:	eb14001f 	cmp	x0, x20
   2b758:	54000040 	b.eq	2b760 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x5a0>  // b.none
   2b75c:	f900c3f4 	str	x20, [sp, #384]
   2b760:	b0ffffd7 	adrp	x23, 24000 <(anonymous namespace)::coarse_gcr_fused_step(std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, double&) [clone ._omp_fn.1]+0x90>
   2b764:	b201f3f8 	mov	x24, #0xaaaaaaaaaaaaaaaa    	// #-6148914691236517206
   2b768:	52800000 	mov	w0, #0x0                   	// #0
   2b76c:	f9004fff 	str	xzr, [sp, #152]
   2b770:	912f82f7 	add	x23, x23, #0xbe0
   2b774:	9106c3f6 	add	x22, sp, #0x1b0
   2b778:	f2955578 	movk	x24, #0xaaab
   2b77c:	b9015fff 	str	wzr, [sp, #348]
   2b780:	910573f9 	add	x25, sp, #0x15c
   2b784:	14000002 	b	2b78c <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x5cc>
   2b788:	f940b3fa 	ldr	x26, [sp, #352]
   2b78c:	52801913 	mov	w19, #0xc8                  	// #200
   2b790:	9b336813 	smaddl	x19, w0, w19, x26
   2b794:	39431261 	ldrb	w1, [x19, #196]
   2b798:	350000c1 	cbnz	w1, 2b7b0 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x5f0>
   2b79c:	6d4a8662 	ldp	d2, d1, [x19, #168]
   2b7a0:	fd452b80 	ldr	d0, [x28, #2640]
   2b7a4:	1e620800 	fmul	d0, d0, d2
   2b7a8:	1e602030 	fcmpe	d1, d0
   2b7ac:	54006b6a 	b.ge	2c518 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1358>  // b.tcont
   2b7b0:	b94097e1 	ldr	w1, [sp, #148]
   2b7b4:	11000400 	add	w0, w0, #0x1
   2b7b8:	b9015fe0 	str	w0, [sp, #348]
   2b7bc:	6b01001f 	cmp	w0, w1
   2b7c0:	54fffe4b 	b.lt	2b788 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x5c8>  // b.tstop
   2b7c4:	f940bff8 	ldr	x24, [sp, #376]
   2b7c8:	eb14031f 	cmp	x24, x20
   2b7cc:	5400aa00 	b.eq	2cd0c <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1b4c>  // b.none
   2b7d0:	f9404fe0 	ldr	x0, [sp, #152]
   2b7d4:	b400abe0 	cbz	x0, 2cd50 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1b90>
   2b7d8:	b940fbe0 	ldr	w0, [sp, #248]
   2b7dc:	b201f3f7 	mov	x23, #0xaaaaaaaaaaaaaaaa    	// #-6148914691236517206
   2b7e0:	d2800016 	mov	x22, #0x0                   	// #0
   2b7e4:	d2800015 	mov	x21, #0x0                   	// #0
   2b7e8:	f2955577 	movk	x23, #0xaaab
   2b7ec:	9106c3fa 	add	x26, sp, #0x1b0
   2b7f0:	11000400 	add	w0, w0, #0x1
   2b7f4:	b9008be0 	str	w0, [sp, #136]
   2b7f8:	f9405be0 	ldr	x0, [sp, #176]
   2b7fc:	eb00037f 	cmp	x27, x0
   2b800:	540000a0 	b.eq	2b814 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x654>  // b.none
   2b804:	f94067e2 	ldr	x2, [sp, #200]
   2b808:	52800001 	mov	w1, #0x0                   	// #0
   2b80c:	aa1b03e0 	mov	x0, x27
   2b810:	97ff662c 	bl	50c0 <memset@plt>
   2b814:	b0ffffd3 	adrp	x19, 24000 <(anonymous namespace)::coarse_gcr_fused_step(std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, double&) [clone ._omp_fn.1]+0x90>
   2b818:	aa1803f9 	mov	x25, x24
   2b81c:	911bc273 	add	x19, x19, #0x6f0
   2b820:	eb18029f 	cmp	x20, x24
   2b824:	54006ec0 	b.eq	2c5fc <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x143c>  // b.none
   2b828:	b9400338 	ldr	w24, [x25]
   2b82c:	f940b3e0 	ldr	x0, [sp, #352]
   2b830:	52801903 	mov	w3, #0xc8                  	// #200
   2b834:	9b230303 	smaddl	x3, w24, w3, x0
   2b838:	a9490860 	ldp	x0, x2, [x3, #144]
   2b83c:	cb000042 	sub	x2, x2, x0
   2b840:	9343fc42 	asr	x2, x2, #3
   2b844:	9b177c42 	mul	x2, x2, x23
   2b848:	eb15005f 	cmp	x2, x21
   2b84c:	540002a9 	b.ls	2b8a0 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x6e0>  // b.plast
   2b850:	8b160005 	add	x5, x0, x22
   2b854:	f8766806 	ldr	x6, [x0, x22]
   2b858:	91018062 	add	x2, x3, #0x60
   2b85c:	aa1a03e1 	mov	x1, x26
   2b860:	f94004a4 	ldr	x4, [x5, #8]
   2b864:	a91b0be5 	stp	x5, x2, [sp, #432]
   2b868:	52800003 	mov	w3, #0x0                   	// #0
   2b86c:	aa1303e0 	mov	x0, x19
   2b870:	a91c7fff 	stp	xzr, xzr, [sp, #448]
   2b874:	531f7b18 	lsl	w24, w24, #1
   2b878:	937d7f18 	sbfiz	x24, x24, #3, #32
   2b87c:	cb060082 	sub	x2, x4, x6
   2b880:	d2835004 	mov	x4, #0x1a80                	// #6784
   2b884:	f2a000c4 	movk	x4, #0x6, lsl #16
   2b888:	eb04005f 	cmp	x2, x4
   2b88c:	1a9f87e2 	cset	w2, ls  // ls = plast
   2b890:	97ff6738 	bl	5570 <GOMP_parallel@plt>
   2b894:	3dc073e0 	ldr	q0, [sp, #448]
   2b898:	6e004000 	ext	v0.16b, v0.16b, v0.16b, #8
   2b89c:	3cb86b60 	str	q0, [x27, x24]
   2b8a0:	91001339 	add	x25, x25, #0x4
   2b8a4:	eb19029f 	cmp	x20, x25
   2b8a8:	54fffc01 	b.ne	2b828 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x668>  // b.any
   2b8ac:	f94057e0 	ldr	x0, [sp, #168]
   2b8b0:	f9475800 	ldr	x0, [x0, #3760]
   2b8b4:	b9400000 	ldr	w0, [x0]
   2b8b8:	7100041f 	cmp	w0, #0x1
   2b8bc:	540060ac 	b.gt	2c4d0 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1310>
   2b8c0:	b9408be0 	ldr	w0, [sp, #136]
   2b8c4:	a957e3f4 	ldp	x20, x24, [sp, #376]
   2b8c8:	b900fbe0 	str	w0, [sp, #248]
   2b8cc:	eb14031f 	cmp	x24, x20
   2b8d0:	54006200 	b.eq	2c510 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1350>  // b.none
   2b8d4:	52801919 	mov	w25, #0xc8                  	// #200
   2b8d8:	b9400282 	ldr	w2, [x20]
   2b8dc:	f940b3f3 	ldr	x19, [sp, #352]
   2b8e0:	9b394c53 	smaddl	x19, w2, w25, x19
   2b8e4:	a9490261 	ldp	x1, x0, [x19, #144]
   2b8e8:	cb010000 	sub	x0, x0, x1
   2b8ec:	9343fc00 	asr	x0, x0, #3
   2b8f0:	9b177c00 	mul	x0, x0, x23
   2b8f4:	eb15001f 	cmp	x0, x21
   2b8f8:	54000249 	b.ls	2b940 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x780>  // b.plast
   2b8fc:	531f7842 	lsl	w2, w2, #1
   2b900:	11000440 	add	w0, w2, #0x1
   2b904:	fc62db69 	ldr	d9, [x27, w2, sxtw #3]
   2b908:	8b160021 	add	x1, x1, x22
   2b90c:	fc60db68 	ldr	d8, [x27, w0, sxtw #3]
   2b910:	91018260 	add	x0, x19, #0x60
   2b914:	1e614129 	fneg	d9, d9
   2b918:	1e614108 	fneg	d8, d8
   2b91c:	1e604120 	fmov	d0, d9
   2b920:	1e604101 	fmov	d1, d8
   2b924:	97ff8797 	bl	d780 <lqcd_native::detail::coarse_axpy(std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::complex<double>, std::vector<float, lqcd_native::WorkspaceAllocator<float> > const&)>
   2b928:	f9403e61 	ldr	x1, [x19, #120]
   2b92c:	1e604120 	fmov	d0, d9
   2b930:	91012260 	add	x0, x19, #0x48
   2b934:	1e604101 	fmov	d1, d8
   2b938:	8b160021 	add	x1, x1, x22
   2b93c:	97ff8791 	bl	d780 <lqcd_native::detail::coarse_axpy(std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::complex<double>, std::vector<float, lqcd_native::WorkspaceAllocator<float> > const&)>
   2b940:	91001294 	add	x20, x20, #0x4
   2b944:	eb14031f 	cmp	x24, x20
   2b948:	54fffc81 	b.ne	2b8d8 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x718>  // b.any
   2b94c:	a957d3f8 	ldp	x24, x20, [sp, #376]
   2b950:	b9408be0 	ldr	w0, [sp, #136]
   2b954:	910006b5 	add	x21, x21, #0x1
   2b958:	910062d6 	add	x22, x22, #0x18
   2b95c:	11000400 	add	w0, w0, #0x1
   2b960:	b9008be0 	str	w0, [sp, #136]
   2b964:	f9404fe0 	ldr	x0, [sp, #152]
   2b968:	eb0002bf 	cmp	x21, x0
   2b96c:	54fff461 	b.ne	2b7f8 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x638>  // b.any
   2b970:	f94063e0 	ldr	x0, [sp, #192]
   2b974:	f94073e1 	ldr	x1, [sp, #224]
   2b978:	eb01001f 	cmp	x0, x1
   2b97c:	540000a0 	b.eq	2b990 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x7d0>  // b.none
   2b980:	f94063e0 	ldr	x0, [sp, #192]
   2b984:	f9406be2 	ldr	x2, [sp, #208]
   2b988:	52800001 	mov	w1, #0x0                   	// #0
   2b98c:	97ff65cd 	bl	50c0 <memset@plt>
   2b990:	eb18029f 	cmp	x20, x24
   2b994:	54000480 	b.eq	2ba24 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x864>  // b.none
   2b998:	f94063f9 	ldr	x25, [sp, #192]
   2b99c:	b0ffffd7 	adrp	x23, 24000 <(anonymous namespace)::coarse_gcr_fused_step(std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, double&) [clone ._omp_fn.1]+0x90>
   2b9a0:	9106c3f3 	add	x19, sp, #0x1b0
   2b9a4:	2f00e408 	movi	d8, #0x0
   2b9a8:	912002f7 	add	x23, x23, #0x800
   2b9ac:	52801915 	mov	w21, #0xc8                  	// #200
   2b9b0:	b8404716 	ldr	w22, [x24], #4
   2b9b4:	f940b3e2 	ldr	x2, [sp, #352]
   2b9b8:	aa1303e1 	mov	x1, x19
   2b9bc:	aa1703e0 	mov	x0, x23
   2b9c0:	52800003 	mov	w3, #0x0                   	// #0
   2b9c4:	9b350ac2 	smaddl	x2, w22, w21, x2
   2b9c8:	0b1606d6 	add	w22, w22, w22, lsl #1
   2b9cc:	f9403046 	ldr	x6, [x2, #96]
   2b9d0:	f9403444 	ldr	x4, [x2, #104]
   2b9d4:	91018045 	add	x5, x2, #0x60
   2b9d8:	91006042 	add	x2, x2, #0x18
   2b9dc:	a91b0be5 	stp	x5, x2, [sp, #432]
   2b9e0:	6d1c23e8 	stp	d8, d8, [sp, #448]
   2b9e4:	fd00ebe8 	str	d8, [sp, #464]
   2b9e8:	8b36cf36 	add	x22, x25, w22, sxtw #3
   2b9ec:	cb060082 	sub	x2, x4, x6
   2b9f0:	d2835004 	mov	x4, #0x1a80                	// #6784
   2b9f4:	f2a000c4 	movk	x4, #0x6, lsl #16
   2b9f8:	eb04005f 	cmp	x2, x4
   2b9fc:	1a9f87e2 	cset	w2, ls  // ls = plast
   2ba00:	97ff66dc 	bl	5570 <GOMP_parallel@plt>
   2ba04:	6d5c87e0 	ldp	d0, d1, [sp, #456]
   2ba08:	6d1b03e1 	stp	d1, d0, [sp, #432]
   2ba0c:	a9400660 	ldp	x0, x1, [x19]
   2ba10:	f9400a62 	ldr	x2, [x19, #16]
   2ba14:	a90006c0 	stp	x0, x1, [x22]
   2ba18:	f9000ac2 	str	x2, [x22, #16]
   2ba1c:	eb18029f 	cmp	x20, x24
   2ba20:	54fffc81 	b.ne	2b9b0 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x7f0>  // b.any
   2ba24:	f94057e0 	ldr	x0, [sp, #168]
   2ba28:	f9475800 	ldr	x0, [x0, #3760]
   2ba2c:	b9400000 	ldr	w0, [x0]
   2ba30:	7100041f 	cmp	w0, #0x1
   2ba34:	5400606c 	b.gt	2c640 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1480>
   2ba38:	f94053e1 	ldr	x1, [sp, #160]
   2ba3c:	f9407be0 	ldr	x0, [sp, #240]
   2ba40:	eb01001f 	cmp	x0, x1
   2ba44:	540000a0 	b.eq	2ba58 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x898>  // b.none
   2ba48:	f94083e2 	ldr	x2, [sp, #256]
   2ba4c:	aa0103e0 	mov	x0, x1
   2ba50:	52800001 	mov	w1, #0x0                   	// #0
   2ba54:	97ff659b 	bl	50c0 <memset@plt>
   2ba58:	a957ebf8 	ldp	x24, x26, [sp, #376]
   2ba5c:	eb18035f 	cmp	x26, x24
   2ba60:	54000760 	b.eq	2bb4c <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x98c>  // b.none
   2ba64:	f90047fb 	str	x27, [sp, #136]
   2ba68:	aa1a03fb 	mov	x27, x26
   2ba6c:	f94053f9 	ldr	x25, [sp, #160]
   2ba70:	b0ffffd3 	adrp	x19, 24000 <(anonymous namespace)::coarse_gcr_fused_step(std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, double&) [clone ._omp_fn.1]+0x90>
   2ba74:	f94063fa 	ldr	x26, [sp, #192]
   2ba78:	9106c3f4 	add	x20, sp, #0x1b0
   2ba7c:	91250273 	add	x19, x19, #0x940
   2ba80:	b9400317 	ldr	w23, [x24]
   2ba84:	f940b3e0 	ldr	x0, [sp, #352]
   2ba88:	52801915 	mov	w21, #0xc8                  	// #200
   2ba8c:	0b1706e2 	add	w2, w23, w23, lsl #1
   2ba90:	9b3502f5 	smaddl	x21, w23, w21, x0
   2ba94:	fc62db40 	ldr	d0, [x26, w2, sxtw #3]
   2ba98:	8b22cf56 	add	x22, x26, w2, sxtw #3
   2ba9c:	1e602008 	fcmp	d0, #0.0
   2baa0:	54004de5 	b.pl	2c45c <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x129c>  // b.nfrst
   2baa4:	97ff6757 	bl	5800 <sqrt@plt>
   2baa8:	1e6a2010 	fcmpe	d0, d10
   2baac:	54004e84 	b.mi	2c47c <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x12bc>  // b.first
   2bab0:	fd4002c0 	ldr	d0, [x22]
   2bab4:	910182a0 	add	x0, x21, #0x60
   2bab8:	910122a5 	add	x5, x21, #0x48
   2babc:	9100c2a4 	add	x4, x21, #0x30
   2bac0:	910062b5 	add	x21, x21, #0x18
   2bac4:	1e602008 	fcmp	d0, #0.0
   2bac8:	54009c05 	b.pl	2ce48 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1c88>  // b.nfrst
   2bacc:	f9004fe4 	str	x4, [sp, #152]
   2bad0:	a91403e5 	stp	x5, x0, [sp, #320]
   2bad4:	97ff674b 	bl	5800 <sqrt@plt>
   2bad8:	f9404fe4 	ldr	x4, [sp, #152]
   2badc:	a95403e5 	ldp	x5, x0, [sp, #320]
   2bae0:	6d4086c2 	ldp	d2, d1, [x22, #8]
   2bae4:	a9400807 	ldp	x7, x2, [x0]
   2bae8:	52800003 	mov	w3, #0x0                   	// #0
   2baec:	aa1403e1 	mov	x1, x20
   2baf0:	fd00ebe0 	str	d0, [sp, #464]
   2baf4:	a91c57e4 	stp	x4, x21, [sp, #448]
   2baf8:	d2835004 	mov	x4, #0x1a80                	// #6784
   2bafc:	f2a000c4 	movk	x4, #0x6, lsl #16
   2bb00:	a91b17e0 	stp	x0, x5, [sp, #432]
   2bb04:	aa1303e0 	mov	x0, x19
   2bb08:	f900efff 	str	xzr, [sp, #472]
   2bb0c:	cb070042 	sub	x2, x2, x7
   2bb10:	eb04005f 	cmp	x2, x4
   2bb14:	1e601842 	fdiv	d2, d2, d0
   2bb18:	1a9f87e2 	cset	w2, ls  // ls = plast
   2bb1c:	1e601820 	fdiv	d0, d1, d0
   2bb20:	1e624041 	fcvt	s1, d2
   2bb24:	1e624000 	fcvt	s0, d0
   2bb28:	bd01e3e1 	str	s1, [sp, #480]
   2bb2c:	bd01e7e0 	str	s0, [sp, #484]
   2bb30:	97ff6690 	bl	5570 <GOMP_parallel@plt>
   2bb34:	fd40efe0 	ldr	d0, [sp, #472]
   2bb38:	fc37db20 	str	d0, [x25, w23, sxtw #3]
   2bb3c:	91001318 	add	x24, x24, #0x4
   2bb40:	eb1b031f 	cmp	x24, x27
   2bb44:	54fff9e1 	b.ne	2ba80 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x8c0>  // b.any
   2bb48:	f94047fb 	ldr	x27, [sp, #136]
   2bb4c:	f94057e0 	ldr	x0, [sp, #168]
   2bb50:	f9475800 	ldr	x0, [x0, #3760]
   2bb54:	b9400000 	ldr	w0, [x0]
   2bb58:	7100041f 	cmp	w0, #0x1
   2bb5c:	540058ac 	b.gt	2c670 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x14b0>
   2bb60:	a95907e0 	ldp	x0, x1, [sp, #400]
   2bb64:	eb01001f 	cmp	x0, x1
   2bb68:	54000040 	b.eq	2bb70 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x9b0>  // b.none
   2bb6c:	f900cfe0 	str	x0, [sp, #408]
   2bb70:	a957d7f4 	ldp	x20, x21, [sp, #376]
   2bb74:	f940b3fa 	ldr	x26, [sp, #352]
   2bb78:	eb15029f 	cmp	x20, x21
   2bb7c:	54005500 	b.eq	2c61c <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x145c>  // b.none
   2bb80:	52801917 	mov	w23, #0xc8                  	// #200
   2bb84:	9106c3f8 	add	x24, sp, #0x1b0
   2bb88:	910573f9 	add	x25, sp, #0x15c
   2bb8c:	1e7e1008 	fmov	d8, #-1.000000000000000000e+00
   2bb90:	b9400280 	ldr	w0, [x20]
   2bb94:	9b376813 	smaddl	x19, w0, w23, x26
   2bb98:	39431261 	ldrb	w1, [x19, #196]
   2bb9c:	b9015fe0 	str	w0, [sp, #348]
   2bba0:	35000581 	cbnz	w1, 2bc50 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xa90>
   2bba4:	f94053e1 	ldr	x1, [sp, #160]
   2bba8:	fc60d820 	ldr	d0, [x1, w0, sxtw #3]
   2bbac:	1e602008 	fcmp	d0, #0.0
   2bbb0:	540046c5 	b.pl	2c488 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x12c8>  // b.nfrst
   2bbb4:	97ff6713 	bl	5800 <sqrt@plt>
   2bbb8:	9101e260 	add	x0, x19, #0x78
   2bbbc:	a9408801 	ldp	x1, x2, [x0, #8]
   2bbc0:	fd005a60 	str	d0, [x19, #176]
   2bbc4:	eb02003f 	cmp	x1, x2
   2bbc8:	540046c0 	b.eq	2c4a0 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x12e0>  // b.none
   2bbcc:	d503201f 	nop
   2bbd0:	aa1303e2 	mov	x2, x19
   2bbd4:	91006023 	add	x3, x1, #0x18
   2bbd8:	3cc48c40 	ldr	q0, [x2, #72]!
   2bbdc:	f9400844 	ldr	x4, [x2, #16]
   2bbe0:	f900085f 	str	xzr, [x2, #16]
   2bbe4:	3d800020 	str	q0, [x1]
   2bbe8:	a904fe7f 	stp	xzr, xzr, [x19, #72]
   2bbec:	f9000824 	str	x4, [x1, #16]
   2bbf0:	f9000403 	str	x3, [x0, #8]
   2bbf4:	91024260 	add	x0, x19, #0x90
   2bbf8:	a9408801 	ldp	x1, x2, [x0, #8]
   2bbfc:	eb02003f 	cmp	x1, x2
   2bc00:	540045c0 	b.eq	2c4b8 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x12f8>  // b.none
   2bc04:	aa1303e3 	mov	x3, x19
   2bc08:	91006022 	add	x2, x1, #0x18
   2bc0c:	3cc60c60 	ldr	q0, [x3, #96]!
   2bc10:	f9400864 	ldr	x4, [x3, #16]
   2bc14:	f900087f 	str	xzr, [x3, #16]
   2bc18:	3d800020 	str	q0, [x1]
   2bc1c:	a9067e7f 	stp	xzr, xzr, [x19, #96]
   2bc20:	f9000824 	str	x4, [x1, #16]
   2bc24:	f9000402 	str	x2, [x0, #8]
   2bc28:	6d4a8662 	ldp	d2, d1, [x19, #168]
   2bc2c:	fd452b80 	ldr	d0, [x28, #2640]
   2bc30:	f9404a60 	ldr	x0, [x19, #144]
   2bc34:	cb000042 	sub	x2, x2, x0
   2bc38:	1e620800 	fmul	d0, d0, d2
   2bc3c:	1e602030 	fcmpe	d1, d0
   2bc40:	54001124 	b.mi	2be64 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xca4>  // b.first
   2bc44:	f106005f 	cmp	x2, #0x180
   2bc48:	540010e0 	b.eq	2be64 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xca4>  // b.none
   2bc4c:	f940b3fa 	ldr	x26, [sp, #352]
   2bc50:	91001294 	add	x20, x20, #0x4
   2bc54:	eb1402bf 	cmp	x21, x20
   2bc58:	54fff9c1 	b.ne	2bb90 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x9d0>  // b.any
   2bc5c:	a95953f6 	ldp	x22, x20, [sp, #400]
   2bc60:	eb1402df 	cmp	x22, x20
   2bc64:	54004dc0 	b.eq	2c61c <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x145c>  // b.none
   2bc68:	f94053e1 	ldr	x1, [sp, #160]
   2bc6c:	f9407be0 	ldr	x0, [sp, #240]
   2bc70:	eb01001f 	cmp	x0, x1
   2bc74:	540000a0 	b.eq	2bc88 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xac8>  // b.none
   2bc78:	f94083e2 	ldr	x2, [sp, #256]
   2bc7c:	aa0103e0 	mov	x0, x1
   2bc80:	52800001 	mov	w1, #0x0                   	// #0
   2bc84:	97ff650f 	bl	50c0 <memset@plt>
   2bc88:	b0ffffd8 	adrp	x24, 24000 <(anonymous namespace)::coarse_gcr_fused_step(std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, double&) [clone ._omp_fn.1]+0x90>
   2bc8c:	9106c3f3 	add	x19, sp, #0x1b0
   2bc90:	2f00e408 	movi	d8, #0x0
   2bc94:	52801915 	mov	w21, #0xc8                  	// #200
   2bc98:	912c4318 	add	x24, x24, #0xb10
   2bc9c:	f94053f7 	ldr	x23, [sp, #160]
   2bca0:	14000002 	b	2bca8 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xae8>
   2bca4:	f940b3fa 	ldr	x26, [sp, #352]
   2bca8:	b84046d9 	ldr	w25, [x22], #4
   2bcac:	52800003 	mov	w3, #0x0                   	// #0
   2bcb0:	aa1303e1 	mov	x1, x19
   2bcb4:	aa1803e0 	mov	x0, x24
   2bcb8:	9b356b22 	smaddl	x2, w25, w21, x26
   2bcbc:	91006044 	add	x4, x2, #0x18
   2bcc0:	a9418845 	ldp	x5, x2, [x2, #24]
   2bcc4:	fd00dfe8 	str	d8, [sp, #440]
   2bcc8:	f900dbe4 	str	x4, [sp, #432]
   2bccc:	d2835004 	mov	x4, #0x1a80                	// #6784
   2bcd0:	f2a000c4 	movk	x4, #0x6, lsl #16
   2bcd4:	cb050042 	sub	x2, x2, x5
   2bcd8:	eb04005f 	cmp	x2, x4
   2bcdc:	1a9f87e2 	cset	w2, ls  // ls = plast
   2bce0:	97ff6624 	bl	5570 <GOMP_parallel@plt>
   2bce4:	fd40dfe0 	ldr	d0, [sp, #440]
   2bce8:	fc39dae0 	str	d0, [x23, w25, sxtw #3]
   2bcec:	eb1402df 	cmp	x22, x20
   2bcf0:	54fffda1 	b.ne	2bca4 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xae4>  // b.any
   2bcf4:	f94057e0 	ldr	x0, [sp, #168]
   2bcf8:	f9475800 	ldr	x0, [x0, #3760]
   2bcfc:	b9400000 	ldr	w0, [x0]
   2bd00:	7100041f 	cmp	w0, #0x1
   2bd04:	54004d6c 	b.gt	2c6b0 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x14f0>
   2bd08:	b940fbe0 	ldr	w0, [sp, #248]
   2bd0c:	a9595ff4 	ldp	x20, x23, [sp, #400]
   2bd10:	52801918 	mov	w24, #0xc8                  	// #200
   2bd14:	11000c00 	add	w0, w0, #0x3
   2bd18:	b900fbe0 	str	w0, [sp, #248]
   2bd1c:	eb1402ff 	cmp	x23, x20
   2bd20:	540005a0 	b.eq	2bdd4 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xc14>  // b.none
   2bd24:	f94053f6 	ldr	x22, [sp, #160]
   2bd28:	f90047fb 	str	x27, [sp, #136]
   2bd2c:	d503201f 	nop
   2bd30:	b9400295 	ldr	w21, [x20]
   2bd34:	f940b3e0 	ldr	x0, [sp, #352]
   2bd38:	fc75dac0 	ldr	d0, [x22, w21, sxtw #3]
   2bd3c:	9b3802b5 	smaddl	x21, w21, w24, x0
   2bd40:	1e602008 	fcmp	d0, #0.0
   2bd44:	54003c25 	b.pl	2c4c8 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1308>  // b.nfrst
   2bd48:	97ff66ae 	bl	5800 <sqrt@plt>
   2bd4c:	d503201f 	nop
   2bd50:	f9404ab9 	ldr	x25, [x21, #144]
   2bd54:	f9404ebb 	ldr	x27, [x21, #152]
   2bd58:	910242ba 	add	x26, x21, #0x90
   2bd5c:	fd005aa0 	str	d0, [x21, #176]
   2bd60:	eb1b033f 	cmp	x25, x27
   2bd64:	54000140 	b.eq	2bd8c <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xbcc>  // b.none
   2bd68:	aa1903f3 	mov	x19, x25
   2bd6c:	d503201f 	nop
   2bd70:	f9400260 	ldr	x0, [x19]
   2bd74:	91006273 	add	x19, x19, #0x18
   2bd78:	b40036c0 	cbz	x0, 2c450 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1290>
   2bd7c:	97ff64c9 	bl	50a0 <free@plt>
   2bd80:	eb1b027f 	cmp	x19, x27
   2bd84:	54ffff61 	b.ne	2bd70 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xbb0>  // b.any
   2bd88:	f9000759 	str	x25, [x26, #8]
   2bd8c:	9101e2b9 	add	x25, x21, #0x78
   2bd90:	f940073a 	ldr	x26, [x25, #8]
   2bd94:	f9403eb5 	ldr	x21, [x21, #120]
   2bd98:	eb1a02bf 	cmp	x21, x26
   2bd9c:	54000140 	b.eq	2bdc4 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xc04>  // b.none
   2bda0:	aa1503f3 	mov	x19, x21
   2bda4:	d503201f 	nop
   2bda8:	f9400260 	ldr	x0, [x19]
   2bdac:	91006273 	add	x19, x19, #0x18
   2bdb0:	b40034a0 	cbz	x0, 2c444 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1284>
   2bdb4:	97ff64bb 	bl	50a0 <free@plt>
   2bdb8:	eb1a027f 	cmp	x19, x26
   2bdbc:	54ffff61 	b.ne	2bda8 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xbe8>  // b.any
   2bdc0:	f9000735 	str	x21, [x25, #8]
   2bdc4:	91001294 	add	x20, x20, #0x4
   2bdc8:	eb1402ff 	cmp	x23, x20
   2bdcc:	54fffb21 	b.ne	2bd30 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xb70>  // b.any
   2bdd0:	f94047fb 	ldr	x27, [sp, #136]
   2bdd4:	f940b3fa 	ldr	x26, [sp, #352]
   2bdd8:	b940ffe1 	ldr	w1, [sp, #252]
   2bddc:	b94b6380 	ldr	w0, [x28, #2912]
   2bde0:	11000421 	add	w1, w1, #0x1
   2bde4:	b900ffe1 	str	w1, [sp, #252]
   2bde8:	6b01001f 	cmp	w0, w1
   2bdec:	54ffcb2c 	b.gt	2b750 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x590>
   2bdf0:	f94063e1 	ldr	x1, [sp, #192]
   2bdf4:	f94073e0 	ldr	x0, [sp, #224]
   2bdf8:	d2800015 	mov	x21, #0x0                   	// #0
   2bdfc:	d2800014 	mov	x20, #0x0                   	// #0
   2be00:	52800013 	mov	w19, #0x0                   	// #0
   2be04:	cb010016 	sub	x22, x0, x1
   2be08:	14000008 	b	2be28 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xc68>
   2be0c:	b94097e0 	ldr	w0, [sp, #148]
   2be10:	11000673 	add	w19, w19, #0x1
   2be14:	91032294 	add	x20, x20, #0xc8
   2be18:	910062b5 	add	x21, x21, #0x18
   2be1c:	6b00027f 	cmp	w19, w0
   2be20:	5400460a 	b.ge	2c6e0 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1520>  // b.tcont
   2be24:	f940b3fa 	ldr	x26, [sp, #352]
   2be28:	8b140342 	add	x2, x26, x20
   2be2c:	fd405440 	ldr	d0, [x2, #168]
   2be30:	1e602008 	fcmp	d0, #0.0
   2be34:	54fffec0 	b.eq	2be0c <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xc4c>  // b.none
   2be38:	f9406fe0 	ldr	x0, [sp, #216]
   2be3c:	9100c042 	add	x2, x2, #0x30
   2be40:	f9006bf6 	str	x22, [sp, #208]
   2be44:	f9400003 	ldr	x3, [x0]
   2be48:	f9405fe0 	ldr	x0, [sp, #184]
   2be4c:	f9400001 	ldr	x1, [x0]
   2be50:	8b150063 	add	x3, x3, x21
   2be54:	aa1c03e0 	mov	x0, x28
   2be58:	8b150021 	add	x1, x1, x21
   2be5c:	97fff14d 	bl	28390 <NativeMG::Impl::coarse_reconstruct(std::vector<float, lqcd_native::WorkspaceAllocator<float> > const&, std::vector<float, lqcd_native::WorkspaceAllocator<float> > const&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&) const>
   2be60:	17ffffeb 	b	2be0c <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xc4c>
   2be64:	29578e64 	ldp	w4, w3, [x19, #188]
   2be68:	f106005f 	cmp	x2, #0x180
   2be6c:	9100c261 	add	x1, x19, #0x30
   2be70:	aa1803e2 	mov	x2, x24
   2be74:	aa1c03e0 	mov	x0, x28
   2be78:	1a841484 	cinc	w4, w4, eq  // eq = none
   2be7c:	11000463 	add	w3, w3, #0x1
   2be80:	29178e64 	stp	w4, w3, [x19, #188]
   2be84:	a91b7fff 	stp	xzr, xzr, [sp, #432]
   2be88:	f900e3ff 	str	xzr, [sp, #448]
   2be8c:	97fff1b9 	bl	28570 <NativeMG::Impl::coarse_schur(std::vector<float, lqcd_native::WorkspaceAllocator<float> > const&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&) const>
   2be90:	91006276 	add	x22, x19, #0x18
   2be94:	aa1303e1 	mov	x1, x19
   2be98:	aa1603e0 	mov	x0, x22
   2be9c:	97ffea85 	bl	268b0 <std::vector<float, lqcd_native::WorkspaceAllocator<float> >::operator=(std::vector<float, lqcd_native::WorkspaceAllocator<float> > const&) [clone .isra.0]>
   2bea0:	aa1803e1 	mov	x1, x24
   2bea4:	1e604100 	fmov	d0, d8
   2bea8:	aa1603e0 	mov	x0, x22
   2beac:	2f00e401 	movi	d1, #0x0
   2beb0:	97ff8634 	bl	d780 <lqcd_native::detail::coarse_axpy(std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::complex<double>, std::vector<float, lqcd_native::WorkspaceAllocator<float> > const&)>
   2beb4:	f940dbe0 	ldr	x0, [sp, #432]
   2beb8:	b4000040 	cbz	x0, 2bec0 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xd00>
   2bebc:	97ff6479 	bl	50a0 <free@plt>
   2bec0:	a95983e1 	ldp	x1, x0, [sp, #408]
   2bec4:	eb00003f 	cmp	x1, x0
   2bec8:	54003ec0 	b.eq	2c6a0 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x14e0>  // b.none
   2becc:	b9415fe0 	ldr	w0, [sp, #348]
   2bed0:	f940b3fa 	ldr	x26, [sp, #352]
   2bed4:	b8004420 	str	w0, [x1], #4
   2bed8:	f900cfe1 	str	x1, [sp, #408]
   2bedc:	17ffff5d 	b	2bc50 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xa90>
   2bee0:	f90053ff 	str	xzr, [sp, #160]
   2bee4:	f9007bff 	str	xzr, [sp, #240]
   2bee8:	f90087ff 	str	xzr, [sp, #264]
   2beec:	a9167fff 	stp	xzr, xzr, [sp, #352]
   2bef0:	f900bbff 	str	xzr, [sp, #368]
   2bef4:	900002a0 	adrp	x0, 7f000 <__FRAME_END__+0x18c0c>
   2bef8:	f90057e0 	str	x0, [sp, #168]
   2befc:	f9475800 	ldr	x0, [x0, #3760]
   2bf00:	b9400000 	ldr	w0, [x0]
   2bf04:	7100041f 	cmp	w0, #0x1
   2bf08:	5400022d 	b.le	2bf4c <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xd8c>
   2bf0c:	f9407be0 	ldr	x0, [sp, #240]
   2bf10:	900002a5 	adrp	x5, 7f000 <__FRAME_END__+0x18c0c>
   2bf14:	900002a4 	adrp	x4, 7f000 <__FRAME_END__+0x18c0c>
   2bf18:	900002a3 	adrp	x3, 7f000 <__FRAME_END__+0x18c0c>
   2bf1c:	f94053e1 	ldr	x1, [sp, #160]
   2bf20:	f94760a5 	ldr	x5, [x5, #3776]
   2bf24:	f9474884 	ldr	x4, [x4, #3728]
   2bf28:	f9478063 	ldr	x3, [x3, #3840]
   2bf2c:	cb010002 	sub	x2, x0, x1
   2bf30:	d2800020 	mov	x0, #0x1                   	// #1
   2bf34:	f94000a5 	ldr	x5, [x5]
   2bf38:	d3438842 	ubfx	x2, x2, #3, #32
   2bf3c:	97ff6511 	bl	5380 <MPI_Allreduce@plt>
   2bf40:	b94097e0 	ldr	w0, [sp, #148]
   2bf44:	7100001f 	cmp	w0, #0x0
   2bf48:	54ffa98c 	b.gt	2b478 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x2b8>
   2bf4c:	f0000180 	adrp	x0, 5e000 <typeinfo name for lqcd::Error+0x9b8>
   2bf50:	52800001 	mov	w1, #0x0                   	// #0
   2bf54:	9101e000 	add	x0, x0, #0x78
   2bf58:	97ff8526 	bl	d3f0 <lqcd_native::detail::setting(char const*, int)>
   2bf5c:	340011a0 	cbz	w0, 2c190 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xfd0>
   2bf60:	900002a0 	adrp	x0, 7f000 <__FRAME_END__+0x18c0c>
   2bf64:	f947c800 	ldr	x0, [x0, #3984]
   2bf68:	b9400000 	ldr	w0, [x0]
   2bf6c:	35001120 	cbnz	w0, 2c190 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xfd0>
   2bf70:	900002b3 	adrp	x19, 7f000 <__FRAME_END__+0x18c0c>
   2bf74:	f0000181 	adrp	x1, 5e000 <typeinfo name for lqcd::Error+0x9b8>
   2bf78:	d2800462 	mov	x2, #0x23                  	// #35
   2bf7c:	f947de60 	ldr	x0, [x19, #4024]
   2bf80:	91022021 	add	x1, x1, #0x88
   2bf84:	97ff64e3 	bl	5310 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2bf88:	f947de60 	ldr	x0, [x19, #4024]
   2bf8c:	b94097e1 	ldr	w1, [sp, #148]
   2bf90:	97ff65d8 	bl	56f0 <std::ostream::operator<<(int)@plt>
   2bf94:	f0000181 	adrp	x1, 5e000 <typeinfo name for lqcd::Error+0x9b8>
   2bf98:	d2800262 	mov	x2, #0x13                  	// #19
   2bf9c:	aa0003f4 	mov	x20, x0
   2bfa0:	9102c021 	add	x1, x1, #0xb0
   2bfa4:	97ff64db 	bl	5310 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2bfa8:	b94b6381 	ldr	w1, [x28, #2912]
   2bfac:	aa1403e0 	mov	x0, x20
   2bfb0:	97ff65d0 	bl	56f0 <std::ostream::operator<<(int)@plt>
   2bfb4:	f0000181 	adrp	x1, 5e000 <typeinfo name for lqcd::Error+0x9b8>
   2bfb8:	d2800282 	mov	x2, #0x14                  	// #20
   2bfbc:	aa0003f4 	mov	x20, x0
   2bfc0:	91032021 	add	x1, x1, #0xc8
   2bfc4:	97ff64d3 	bl	5310 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2bfc8:	fd452b80 	ldr	d0, [x28, #2640]
   2bfcc:	aa1403e0 	mov	x0, x20
   2bfd0:	97ff6594 	bl	5620 <std::ostream& std::ostream::_M_insert<double>(double)@plt>
   2bfd4:	f0000181 	adrp	x1, 5e000 <typeinfo name for lqcd::Error+0x9b8>
   2bfd8:	d2800282 	mov	x2, #0x14                  	// #20
   2bfdc:	aa0003f4 	mov	x20, x0
   2bfe0:	91038021 	add	x1, x1, #0xe0
   2bfe4:	97ff64cb 	bl	5310 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2bfe8:	aa1403e0 	mov	x0, x20
   2bfec:	52800021 	mov	w1, #0x1                   	// #1
   2bff0:	97ff65c0 	bl	56f0 <std::ostream::operator<<(int)@plt>
   2bff4:	f0000181 	adrp	x1, 5e000 <typeinfo name for lqcd::Error+0x9b8>
   2bff8:	d2800262 	mov	x2, #0x13                  	// #19
   2bffc:	aa0003f4 	mov	x20, x0
   2c000:	9103e021 	add	x1, x1, #0xf8
   2c004:	97ff64c3 	bl	5310 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2c008:	f94057e0 	ldr	x0, [sp, #168]
   2c00c:	f9475801 	ldr	x1, [x0, #3760]
   2c010:	aa1403e0 	mov	x0, x20
   2c014:	b9400021 	ldr	w1, [x1]
   2c018:	7100043f 	cmp	w1, #0x1
   2c01c:	1a9fd7e1 	cset	w1, gt
   2c020:	97ff65b4 	bl	56f0 <std::ostream::operator<<(int)@plt>
   2c024:	900002a0 	adrp	x0, 80000 <std::ostream::put(char)@GLIBCXX_3.4>
   2c028:	910643e1 	add	x1, sp, #0x190
   2c02c:	d0000198 	adrp	x24, 5e000 <typeinfo name for lqcd::Error+0x9b8>
   2c030:	9117e000 	add	x0, x0, #0x5f8
   2c034:	d0000195 	adrp	x21, 5e000 <typeinfo name for lqcd::Error+0x9b8>
   2c038:	aa0103f7 	mov	x23, x1
   2c03c:	4c40a000 	ld1	{v0.16b, v1.16b}, [x0]
   2c040:	91046318 	add	x24, x24, #0x118
   2c044:	910482b5 	add	x21, x21, #0x120
   2c048:	52800014 	mov	w20, #0x0                   	// #0
   2c04c:	d0000199 	adrp	x25, 5e000 <typeinfo name for lqcd::Error+0x9b8>
   2c050:	4c00a020 	st1	{v0.16b, v1.16b}, [x1]
   2c054:	f947de60 	ldr	x0, [x19, #4024]
   2c058:	d2800042 	mov	x2, #0x2                   	// #2
   2c05c:	91044321 	add	x1, x25, #0x110
   2c060:	97ff64ac 	bl	5310 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2c064:	f94002f6 	ldr	x22, [x23]
   2c068:	b4006a96 	cbz	x22, 2cdb8 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1bf8>
   2c06c:	aa1603e0 	mov	x0, x22
   2c070:	97ff63c8 	bl	4f90 <strlen@plt>
   2c074:	aa0003e2 	mov	x2, x0
   2c078:	f947de60 	ldr	x0, [x19, #4024]
   2c07c:	aa1603e1 	mov	x1, x22
   2c080:	97ff64a4 	bl	5310 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2c084:	f947de60 	ldr	x0, [x19, #4024]
   2c088:	d2800062 	mov	x2, #0x3                   	// #3
   2c08c:	aa1803e1 	mov	x1, x24
   2c090:	97ff64a0 	bl	5310 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2c094:	b94097e0 	ldr	w0, [sp, #148]
   2c098:	7100001f 	cmp	w0, #0x0
   2c09c:	5400042d 	b.le	2c120 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xf60>
   2c0a0:	d000019b 	adrp	x27, 5e000 <typeinfo name for lqcd::Error+0x9b8>
   2c0a4:	52800016 	mov	w22, #0x0                   	// #0
   2c0a8:	d280001a 	mov	x26, #0x0                   	// #0
   2c0ac:	91134360 	add	x0, x27, #0x4d0
   2c0b0:	f90047e0 	str	x0, [sp, #136]
   2c0b4:	340011f4 	cbz	w20, 2c2f0 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1130>
   2c0b8:	7100069f 	cmp	w20, #0x1
   2c0bc:	54001760 	b.eq	2c3a8 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x11e8>  // b.none
   2c0c0:	71000a9f 	cmp	w20, #0x2
   2c0c4:	54001a60 	b.eq	2c410 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1250>  // b.none
   2c0c8:	f940b3e0 	ldr	x0, [sp, #352]
   2c0cc:	8b1a0000 	add	x0, x0, x26
   2c0d0:	39431001 	ldrb	w1, [x0, #196]
   2c0d4:	35006121 	cbnz	w1, 2ccf8 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1b38>
   2c0d8:	b940b801 	ldr	w1, [x0, #184]
   2c0dc:	b94b6382 	ldr	w2, [x28, #2912]
   2c0e0:	5280001b 	mov	w27, #0x0                   	// #0
   2c0e4:	6b01005f 	cmp	w2, w1
   2c0e8:	54001a20 	b.eq	2c42c <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x126c>  // b.none
   2c0ec:	340060b6 	cbz	w22, 2cd00 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1b40>
   2c0f0:	d2800022 	mov	x2, #0x1                   	// #1
   2c0f4:	aa1503e1 	mov	x1, x21
   2c0f8:	f947de60 	ldr	x0, [x19, #4024]
   2c0fc:	97ff6485 	bl	5310 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2c100:	f947de60 	ldr	x0, [x19, #4024]
   2c104:	2a1b03e1 	mov	w1, w27
   2c108:	97ff657a 	bl	56f0 <std::ostream::operator<<(int)@plt>
   2c10c:	b94097e0 	ldr	w0, [sp, #148]
   2c110:	110006d6 	add	w22, w22, #0x1
   2c114:	9103235a 	add	x26, x26, #0xc8
   2c118:	6b16001f 	cmp	w0, w22
   2c11c:	54fffd61 	b.ne	2c0c8 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xf08>  // b.any
   2c120:	f947de60 	ldr	x0, [x19, #4024]
   2c124:	52800ba3 	mov	w3, #0x5d                  	// #93
   2c128:	d2800022 	mov	x2, #0x1                   	// #1
   2c12c:	91056be1 	add	x1, sp, #0x15a
   2c130:	39056be3 	strb	w3, [sp, #346]
   2c134:	97ff6477 	bl	5310 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2c138:	11000694 	add	w20, w20, #0x1
   2c13c:	910022f7 	add	x23, x23, #0x8
   2c140:	7100129f 	cmp	w20, #0x4
   2c144:	54fff881 	b.ne	2c054 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xe94>  // b.any
   2c148:	f947de60 	ldr	x0, [x19, #4024]
   2c14c:	52800fa3 	mov	w3, #0x7d                  	// #125
   2c150:	d2800022 	mov	x2, #0x1                   	// #1
   2c154:	9105e3e1 	add	x1, sp, #0x178
   2c158:	3905e3e3 	strb	w3, [sp, #376]
   2c15c:	97ff646d 	bl	5310 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2c160:	aa0003f4 	mov	x20, x0
   2c164:	f9400000 	ldr	x0, [x0]
   2c168:	f85e8000 	ldur	x0, [x0, #-24]
   2c16c:	8b000280 	add	x0, x20, x0
   2c170:	f9407813 	ldr	x19, [x0, #240]
   2c174:	b4006633 	cbz	x19, 2ce38 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1c78>
   2c178:	3940e260 	ldrb	w0, [x19, #56]
   2c17c:	34006340 	cbz	w0, 2cde4 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1c24>
   2c180:	39410e61 	ldrb	w1, [x19, #67]
   2c184:	aa1403e0 	mov	x0, x20
   2c188:	97ff6342 	bl	4e90 <std::ostream::put(char)@plt>
   2c18c:	97ff63f9 	bl	5170 <std::ostream::flush()@plt>
   2c190:	f94053e0 	ldr	x0, [sp, #160]
   2c194:	b4000080 	cbz	x0, 2c1a4 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xfe4>
   2c198:	f94087e1 	ldr	x1, [sp, #264]
   2c19c:	cb000021 	sub	x1, x1, x0
   2c1a0:	97ff6434 	bl	5270 <operator delete(void*, unsigned long)@plt>
   2c1a4:	a9565bf4 	ldp	x20, x22, [sp, #352]
   2c1a8:	eb16029f 	cmp	x20, x22
   2c1ac:	54000680 	b.eq	2c27c <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x10bc>  // b.none
   2c1b0:	a9495693 	ldp	x19, x21, [x20, #144]
   2c1b4:	eb15027f 	cmp	x19, x21
   2c1b8:	54000120 	b.eq	2c1dc <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x101c>  // b.none
   2c1bc:	d503201f 	nop
   2c1c0:	f9400260 	ldr	x0, [x19]
   2c1c4:	91006273 	add	x19, x19, #0x18
   2c1c8:	b4002120 	cbz	x0, 2c5ec <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x142c>
   2c1cc:	97ff63b5 	bl	50a0 <free@plt>
   2c1d0:	eb15027f 	cmp	x19, x21
   2c1d4:	54ffff61 	b.ne	2c1c0 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1000>  // b.any
   2c1d8:	f9404a95 	ldr	x21, [x20, #144]
   2c1dc:	b40000b5 	cbz	x21, 2c1f0 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1030>
   2c1e0:	f9405281 	ldr	x1, [x20, #160]
   2c1e4:	aa1503e0 	mov	x0, x21
   2c1e8:	cb150021 	sub	x1, x1, x21
   2c1ec:	97ff6421 	bl	5270 <operator delete(void*, unsigned long)@plt>
   2c1f0:	a947d693 	ldp	x19, x21, [x20, #120]
   2c1f4:	eb15027f 	cmp	x19, x21
   2c1f8:	54000120 	b.eq	2c21c <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x105c>  // b.none
   2c1fc:	d503201f 	nop
   2c200:	f9400260 	ldr	x0, [x19]
   2c204:	91006273 	add	x19, x19, #0x18
   2c208:	b4001ea0 	cbz	x0, 2c5dc <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x141c>
   2c20c:	97ff63a5 	bl	50a0 <free@plt>
   2c210:	eb1302bf 	cmp	x21, x19
   2c214:	54ffff61 	b.ne	2c200 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1040>  // b.any
   2c218:	f9403e95 	ldr	x21, [x20, #120]
   2c21c:	b40000b5 	cbz	x21, 2c230 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1070>
   2c220:	f9404681 	ldr	x1, [x20, #136]
   2c224:	aa1503e0 	mov	x0, x21
   2c228:	cb150021 	sub	x1, x1, x21
   2c22c:	97ff6411 	bl	5270 <operator delete(void*, unsigned long)@plt>
   2c230:	f9403280 	ldr	x0, [x20, #96]
   2c234:	b4000040 	cbz	x0, 2c23c <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x107c>
   2c238:	97ff639a 	bl	50a0 <free@plt>
   2c23c:	f9402680 	ldr	x0, [x20, #72]
   2c240:	b4000040 	cbz	x0, 2c248 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1088>
   2c244:	97ff6397 	bl	50a0 <free@plt>
   2c248:	f9401a80 	ldr	x0, [x20, #48]
   2c24c:	b4000040 	cbz	x0, 2c254 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1094>
   2c250:	97ff6394 	bl	50a0 <free@plt>
   2c254:	f9400e80 	ldr	x0, [x20, #24]
   2c258:	b4000040 	cbz	x0, 2c260 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x10a0>
   2c25c:	97ff6391 	bl	50a0 <free@plt>
   2c260:	f9400280 	ldr	x0, [x20]
   2c264:	91032294 	add	x20, x20, #0xc8
   2c268:	b4005400 	cbz	x0, 2cce8 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1b28>
   2c26c:	97ff638d 	bl	50a0 <free@plt>
   2c270:	eb16029f 	cmp	x20, x22
   2c274:	54fff9e1 	b.ne	2c1b0 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xff0>  // b.any
   2c278:	f940b3f6 	ldr	x22, [sp, #352]
   2c27c:	b40000b6 	cbz	x22, 2c290 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x10d0>
   2c280:	f940bbe1 	ldr	x1, [sp, #368]
   2c284:	aa1603e0 	mov	x0, x22
   2c288:	cb160021 	sub	x1, x1, x22
   2c28c:	97ff63f9 	bl	5270 <operator delete(void*, unsigned long)@plt>
   2c290:	b94137e0 	ldr	w0, [sp, #308]
   2c294:	34ff7e20 	cbz	w0, 2b258 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x98>
   2c298:	6d4627e8 	ldp	d8, d9, [sp, #96]
   2c29c:	fd403bea 	ldr	d10, [sp, #112]
   2c2a0:	b94133e0 	ldr	w0, [sp, #304]
   2c2a4:	a94153f3 	ldp	x19, x20, [sp, #16]
   2c2a8:	a9425bf5 	ldp	x21, x22, [sp, #32]
   2c2ac:	a94363f7 	ldp	x23, x24, [sp, #48]
   2c2b0:	a9446bf9 	ldp	x25, x26, [sp, #64]
   2c2b4:	a94573fb 	ldp	x27, x28, [sp, #80]
   2c2b8:	a8df7bfd 	ldp	x29, x30, [sp], #496
   2c2bc:	17ff6409 	b	52e0 <omp_set_num_threads@plt>
   2c2c0:	d2800022 	mov	x2, #0x1                   	// #1
   2c2c4:	aa1503e1 	mov	x1, x21
   2c2c8:	f947de60 	ldr	x0, [x19, #4024]
   2c2cc:	97ff6411 	bl	5310 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2c2d0:	f947de60 	ldr	x0, [x19, #4024]
   2c2d4:	2a1b03e1 	mov	w1, w27
   2c2d8:	97ff6506 	bl	56f0 <std::ostream::operator<<(int)@plt>
   2c2dc:	b94097e0 	ldr	w0, [sp, #148]
   2c2e0:	110006d6 	add	w22, w22, #0x1
   2c2e4:	9103235a 	add	x26, x26, #0xc8
   2c2e8:	6b0002df 	cmp	w22, w0
   2c2ec:	54fff1a0 	b.eq	2c120 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xf60>  // b.none
   2c2f0:	f940b3e0 	ldr	x0, [sp, #352]
   2c2f4:	8b1a0000 	add	x0, x0, x26
   2c2f8:	b940b81b 	ldr	w27, [x0, #184]
   2c2fc:	35fffe36 	cbnz	w22, 2c2c0 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1100>
   2c300:	d2800002 	mov	x2, #0x0                   	// #0
   2c304:	f94047e1 	ldr	x1, [sp, #136]
   2c308:	17fffff0 	b	2c2c8 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1108>
   2c30c:	97ff637d 	bl	5100 <omp_in_parallel@plt>
   2c310:	7100001f 	cmp	w0, #0x0
   2c314:	b94133e1 	ldr	w1, [sp, #304]
   2c318:	7a410260 	ccmp	w19, w1, #0x0, eq  // eq = none
   2c31c:	1a9fc7e0 	cset	w0, le
   2c320:	6b01027f 	cmp	w19, w1
   2c324:	1a9f07e1 	cset	w1, ne  // ne = any
   2c328:	6a000020 	ands	w0, w1, w0
   2c32c:	b90137e0 	str	w0, [sp, #308]
   2c330:	54ff7bc0 	b.eq	2b2a8 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xe8>  // b.none
   2c334:	2a1303e0 	mov	w0, w19
   2c338:	97ff63ea 	bl	52e0 <omp_set_num_threads@plt>
   2c33c:	17fffbdc 	b	2b2ac <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xec>
   2c340:	f0000285 	adrp	x5, 7f000 <__FRAME_END__+0x18c0c>
   2c344:	f0000284 	adrp	x4, 7f000 <__FRAME_END__+0x18c0c>
   2c348:	f0000283 	adrp	x3, 7f000 <__FRAME_END__+0x18c0c>
   2c34c:	f94053e1 	ldr	x1, [sp, #160]
   2c350:	f94760a5 	ldr	x5, [x5, #3776]
   2c354:	f9407be0 	ldr	x0, [sp, #240]
   2c358:	f9474884 	ldr	x4, [x4, #3728]
   2c35c:	f9478063 	ldr	x3, [x3, #3840]
   2c360:	f94000a5 	ldr	x5, [x5]
   2c364:	cb010002 	sub	x2, x0, x1
   2c368:	d2800020 	mov	x0, #0x1                   	// #1
   2c36c:	d3438842 	ubfx	x2, x2, #3, #32
   2c370:	97ff6404 	bl	5380 <MPI_Allreduce@plt>
   2c374:	17fffc9b 	b	2b5e0 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x420>
   2c378:	f94047e1 	ldr	x1, [sp, #136]
   2c37c:	d2800002 	mov	x2, #0x0                   	// #0
   2c380:	f947de60 	ldr	x0, [x19, #4024]
   2c384:	97ff63e3 	bl	5310 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2c388:	f947de60 	ldr	x0, [x19, #4024]
   2c38c:	2a1b03e1 	mov	w1, w27
   2c390:	97ff64d8 	bl	56f0 <std::ostream::operator<<(int)@plt>
   2c394:	b94097e0 	ldr	w0, [sp, #148]
   2c398:	110006d6 	add	w22, w22, #0x1
   2c39c:	9103235a 	add	x26, x26, #0xc8
   2c3a0:	6b16001f 	cmp	w0, w22
   2c3a4:	54ffebe0 	b.eq	2c120 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xf60>  // b.none
   2c3a8:	f940b3e0 	ldr	x0, [sp, #352]
   2c3ac:	8b1a0000 	add	x0, x0, x26
   2c3b0:	b940bc1b 	ldr	w27, [x0, #188]
   2c3b4:	34fffe36 	cbz	w22, 2c378 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x11b8>
   2c3b8:	d2800022 	mov	x2, #0x1                   	// #1
   2c3bc:	aa1503e1 	mov	x1, x21
   2c3c0:	17fffff0 	b	2c380 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x11c0>
   2c3c4:	b94097e0 	ldr	w0, [sp, #148]
   2c3c8:	d280001b 	mov	x27, #0x0                   	// #0
   2c3cc:	f9005bff 	str	xzr, [sp, #176]
   2c3d0:	f9009fff 	str	xzr, [sp, #312]
   2c3d4:	0b000260 	add	w0, w19, w0
   2c3d8:	93407c00 	sxtw	x0, w0
   2c3dc:	17fffcb9 	b	2b6c0 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x500>
   2c3e0:	f94047e1 	ldr	x1, [sp, #136]
   2c3e4:	d2800002 	mov	x2, #0x0                   	// #0
   2c3e8:	f947de60 	ldr	x0, [x19, #4024]
   2c3ec:	97ff63c9 	bl	5310 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2c3f0:	f947de60 	ldr	x0, [x19, #4024]
   2c3f4:	2a1b03e1 	mov	w1, w27
   2c3f8:	97ff64be 	bl	56f0 <std::ostream::operator<<(int)@plt>
   2c3fc:	b94097e0 	ldr	w0, [sp, #148]
   2c400:	110006d6 	add	w22, w22, #0x1
   2c404:	9103235a 	add	x26, x26, #0xc8
   2c408:	6b16001f 	cmp	w0, w22
   2c40c:	54ffe8a0 	b.eq	2c120 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xf60>  // b.none
   2c410:	f940b3e0 	ldr	x0, [sp, #352]
   2c414:	8b1a0000 	add	x0, x0, x26
   2c418:	b940c01b 	ldr	w27, [x0, #192]
   2c41c:	34fffe36 	cbz	w22, 2c3e0 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1220>
   2c420:	d2800022 	mov	x2, #0x1                   	// #1
   2c424:	aa1503e1 	mov	x1, x21
   2c428:	17fffff0 	b	2c3e8 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1228>
   2c42c:	6d4a8400 	ldp	d0, d1, [x0, #168]
   2c430:	fd452b82 	ldr	d2, [x28, #2640]
   2c434:	1e620800 	fmul	d0, d0, d2
   2c438:	1e612010 	fcmpe	d0, d1
   2c43c:	1a9f87fb 	cset	w27, ls  // ls = plast
   2c440:	17ffff2b 	b	2c0ec <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xf2c>
   2c444:	eb13035f 	cmp	x26, x19
   2c448:	54ffcb01 	b.ne	2bda8 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xbe8>  // b.any
   2c44c:	17fffe5d 	b	2bdc0 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xc00>
   2c450:	eb13037f 	cmp	x27, x19
   2c454:	54ffc8e1 	b.ne	2bd70 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xbb0>  // b.any
   2c458:	17fffe4c 	b	2bd88 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xbc8>
   2c45c:	1e61c000 	fsqrt	d0, d0
   2c460:	1e6a2010 	fcmpe	d0, d10
   2c464:	540000c4 	b.mi	2c47c <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x12bc>  // b.first
   2c468:	910182a0 	add	x0, x21, #0x60
   2c46c:	910122a5 	add	x5, x21, #0x48
   2c470:	9100c2a4 	add	x4, x21, #0x30
   2c474:	910062b5 	add	x21, x21, #0x18
   2c478:	17fffd9a 	b	2bae0 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x920>
   2c47c:	52800020 	mov	w0, #0x1                   	// #1
   2c480:	390312a0 	strb	w0, [x21, #196]
   2c484:	17fffdae 	b	2bb3c <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x97c>
   2c488:	1e61c000 	fsqrt	d0, d0
   2c48c:	9101e260 	add	x0, x19, #0x78
   2c490:	a9408801 	ldp	x1, x2, [x0, #8]
   2c494:	fd005a60 	str	d0, [x19, #176]
   2c498:	eb02003f 	cmp	x1, x2
   2c49c:	54ffb9a1 	b.ne	2bbd0 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xa10>  // b.any
   2c4a0:	91012262 	add	x2, x19, #0x48
   2c4a4:	97fffaa3 	bl	2af30 <void std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >::_M_realloc_insert<std::vector<float, lqcd_native::WorkspaceAllocator<float> > >(__gnu_cxx::__normal_iterator<std::vector<float, lqcd_native::WorkspaceAllocator<float> >*, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > >, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&&)>
   2c4a8:	91024260 	add	x0, x19, #0x90
   2c4ac:	a9408801 	ldp	x1, x2, [x0, #8]
   2c4b0:	eb02003f 	cmp	x1, x2
   2c4b4:	54ffba81 	b.ne	2bc04 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xa44>  // b.any
   2c4b8:	91018262 	add	x2, x19, #0x60
   2c4bc:	97fffa9d 	bl	2af30 <void std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >::_M_realloc_insert<std::vector<float, lqcd_native::WorkspaceAllocator<float> > >(__gnu_cxx::__normal_iterator<std::vector<float, lqcd_native::WorkspaceAllocator<float> >*, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > >, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&&)>
   2c4c0:	f9404e62 	ldr	x2, [x19, #152]
   2c4c4:	17fffdd9 	b	2bc28 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xa68>
   2c4c8:	1e61c000 	fsqrt	d0, d0
   2c4cc:	17fffe21 	b	2bd50 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xb90>
   2c4d0:	f0000285 	adrp	x5, 7f000 <__FRAME_END__+0x18c0c>
   2c4d4:	f0000284 	adrp	x4, 7f000 <__FRAME_END__+0x18c0c>
   2c4d8:	f0000283 	adrp	x3, 7f000 <__FRAME_END__+0x18c0c>
   2c4dc:	b940ebe2 	ldr	w2, [sp, #232]
   2c4e0:	f94760a5 	ldr	x5, [x5, #3776]
   2c4e4:	f9474884 	ldr	x4, [x4, #3728]
   2c4e8:	aa1b03e1 	mov	x1, x27
   2c4ec:	d2800020 	mov	x0, #0x1                   	// #1
   2c4f0:	f9478063 	ldr	x3, [x3, #3840]
   2c4f4:	f94000a5 	ldr	x5, [x5]
   2c4f8:	97ff63a2 	bl	5380 <MPI_Allreduce@plt>
   2c4fc:	b9408be0 	ldr	w0, [sp, #136]
   2c500:	a957e3f4 	ldp	x20, x24, [sp, #376]
   2c504:	b900fbe0 	str	w0, [sp, #248]
   2c508:	eb14031f 	cmp	x24, x20
   2c50c:	54ff9e41 	b.ne	2b8d4 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x714>  // b.any
   2c510:	aa1403f8 	mov	x24, x20
   2c514:	17fffd0f 	b	2b950 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x790>
   2c518:	f940c7e1 	ldr	x1, [sp, #392]
   2c51c:	eb14003f 	cmp	x1, x20
   2c520:	54000860 	b.eq	2c62c <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x146c>  // b.none
   2c524:	b8004680 	str	w0, [x20], #4
   2c528:	f900c3f4 	str	x20, [sp, #384]
   2c52c:	b940ba60 	ldr	w0, [x19, #184]
   2c530:	395ec781 	ldrb	w1, [x28, #1969]
   2c534:	91006275 	add	x21, x19, #0x18
   2c538:	91012274 	add	x20, x19, #0x48
   2c53c:	11000400 	add	w0, w0, #0x1
   2c540:	b900ba60 	str	w0, [x19, #184]
   2c544:	340000a1 	cbz	w1, 2c558 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1398>
   2c548:	395f6380 	ldrb	w0, [x28, #2008]
   2c54c:	35000060 	cbnz	w0, 2c558 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1398>
   2c550:	aa1c03e0 	mov	x0, x28
   2c554:	97ffec93 	bl	277a0 <NativeMG::Impl::prepare_coarse_columns() const [clone .part.1]>
   2c558:	f94006a1 	ldr	x1, [x21, #8]
   2c55c:	f9400e63 	ldr	x3, [x19, #24]
   2c560:	aa1603e2 	mov	x2, x22
   2c564:	aa1403e0 	mov	x0, x20
   2c568:	b901b3ff 	str	wzr, [sp, #432]
   2c56c:	cb030021 	sub	x1, x1, x3
   2c570:	9342fc21 	asr	x1, x1, #2
   2c574:	97fff773 	bl	2a340 <std::vector<float, lqcd_native::WorkspaceAllocator<float> >::_M_fill_assign(unsigned long, float const&)>
   2c578:	52800024 	mov	w4, #0x1                   	// #1
   2c57c:	52800002 	mov	w2, #0x0                   	// #0
   2c580:	aa1603e1 	mov	x1, x22
   2c584:	a91b53f5 	stp	x21, x20, [sp, #432]
   2c588:	aa1703e0 	mov	x0, x23
   2c58c:	52800003 	mov	w3, #0x0                   	// #0
   2c590:	f900e3fc 	str	x28, [sp, #448]
   2c594:	b901cbff 	str	wzr, [sp, #456]
   2c598:	390733e4 	strb	w4, [sp, #460]
   2c59c:	97ff63f5 	bl	5570 <GOMP_parallel@plt>
   2c5a0:	aa1403e1 	mov	x1, x20
   2c5a4:	91018262 	add	x2, x19, #0x60
   2c5a8:	aa1c03e0 	mov	x0, x28
   2c5ac:	97ffeff1 	bl	28570 <NativeMG::Impl::coarse_schur(std::vector<float, lqcd_native::WorkspaceAllocator<float> > const&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&) const>
   2c5b0:	a9490662 	ldp	x2, x1, [x19, #144]
   2c5b4:	b9415fe0 	ldr	w0, [sp, #348]
   2c5b8:	f940c3f4 	ldr	x20, [sp, #384]
   2c5bc:	cb020021 	sub	x1, x1, x2
   2c5c0:	f9404fe2 	ldr	x2, [sp, #152]
   2c5c4:	9343fc21 	asr	x1, x1, #3
   2c5c8:	9b187c21 	mul	x1, x1, x24
   2c5cc:	eb01005f 	cmp	x2, x1
   2c5d0:	9a812041 	csel	x1, x2, x1, cs  // cs = hs, nlast
   2c5d4:	f9004fe1 	str	x1, [sp, #152]
   2c5d8:	17fffc76 	b	2b7b0 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x5f0>
   2c5dc:	eb1302bf 	cmp	x21, x19
   2c5e0:	54ffe101 	b.ne	2c200 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1040>  // b.any
   2c5e4:	f9403e95 	ldr	x21, [x20, #120]
   2c5e8:	17ffff0d 	b	2c21c <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x105c>
   2c5ec:	eb1302bf 	cmp	x21, x19
   2c5f0:	54ffde81 	b.ne	2c1c0 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1000>  // b.any
   2c5f4:	f9404a95 	ldr	x21, [x20, #144]
   2c5f8:	17fffef9 	b	2c1dc <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x101c>
   2c5fc:	f94057e0 	ldr	x0, [sp, #168]
   2c600:	f9475800 	ldr	x0, [x0, #3760]
   2c604:	b9400000 	ldr	w0, [x0]
   2c608:	7100041f 	cmp	w0, #0x1
   2c60c:	54fff62c 	b.gt	2c4d0 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1310>
   2c610:	b9408be0 	ldr	w0, [sp, #136]
   2c614:	b900fbe0 	str	w0, [sp, #248]
   2c618:	17fffcce 	b	2b950 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x790>
   2c61c:	b940fbe0 	ldr	w0, [sp, #248]
   2c620:	11000800 	add	w0, w0, #0x2
   2c624:	b900fbe0 	str	w0, [sp, #248]
   2c628:	17fffdec 	b	2bdd8 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xc18>
   2c62c:	f9408fe0 	ldr	x0, [sp, #280]
   2c630:	aa1403e1 	mov	x1, x20
   2c634:	aa1903e2 	mov	x2, x25
   2c638:	97ff626a 	bl	4fe0 <void std::vector<int, std::allocator<int> >::_M_realloc_insert<int const&>(__gnu_cxx::__normal_iterator<int*, std::vector<int, std::allocator<int> > >, int const&)@plt>
   2c63c:	17ffffbc 	b	2c52c <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x136c>
   2c640:	f0000285 	adrp	x5, 7f000 <__FRAME_END__+0x18c0c>
   2c644:	f0000284 	adrp	x4, 7f000 <__FRAME_END__+0x18c0c>
   2c648:	f0000283 	adrp	x3, 7f000 <__FRAME_END__+0x18c0c>
   2c64c:	b94123e2 	ldr	w2, [sp, #288]
   2c650:	f94760a5 	ldr	x5, [x5, #3776]
   2c654:	f9474884 	ldr	x4, [x4, #3728]
   2c658:	d2800020 	mov	x0, #0x1                   	// #1
   2c65c:	f9478063 	ldr	x3, [x3, #3840]
   2c660:	f94063e1 	ldr	x1, [sp, #192]
   2c664:	f94000a5 	ldr	x5, [x5]
   2c668:	97ff6346 	bl	5380 <MPI_Allreduce@plt>
   2c66c:	17fffcf3 	b	2ba38 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x878>
   2c670:	f0000285 	adrp	x5, 7f000 <__FRAME_END__+0x18c0c>
   2c674:	f0000284 	adrp	x4, 7f000 <__FRAME_END__+0x18c0c>
   2c678:	f0000283 	adrp	x3, 7f000 <__FRAME_END__+0x18c0c>
   2c67c:	b94113e2 	ldr	w2, [sp, #272]
   2c680:	f94760a5 	ldr	x5, [x5, #3776]
   2c684:	f9474884 	ldr	x4, [x4, #3728]
   2c688:	d2800020 	mov	x0, #0x1                   	// #1
   2c68c:	f9478063 	ldr	x3, [x3, #3840]
   2c690:	f94053e1 	ldr	x1, [sp, #160]
   2c694:	f94000a5 	ldr	x5, [x5]
   2c698:	97ff633a 	bl	5380 <MPI_Allreduce@plt>
   2c69c:	17fffd31 	b	2bb60 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x9a0>
   2c6a0:	f94097e0 	ldr	x0, [sp, #296]
   2c6a4:	aa1903e2 	mov	x2, x25
   2c6a8:	97ff624e 	bl	4fe0 <void std::vector<int, std::allocator<int> >::_M_realloc_insert<int const&>(__gnu_cxx::__normal_iterator<int*, std::vector<int, std::allocator<int> > >, int const&)@plt>
   2c6ac:	17fffd68 	b	2bc4c <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xa8c>
   2c6b0:	f0000285 	adrp	x5, 7f000 <__FRAME_END__+0x18c0c>
   2c6b4:	f0000284 	adrp	x4, 7f000 <__FRAME_END__+0x18c0c>
   2c6b8:	f0000283 	adrp	x3, 7f000 <__FRAME_END__+0x18c0c>
   2c6bc:	b94113e2 	ldr	w2, [sp, #272]
   2c6c0:	f94760a5 	ldr	x5, [x5, #3776]
   2c6c4:	f9474884 	ldr	x4, [x4, #3728]
   2c6c8:	d2800020 	mov	x0, #0x1                   	// #1
   2c6cc:	f9478063 	ldr	x3, [x3, #3840]
   2c6d0:	f94053e1 	ldr	x1, [sp, #160]
   2c6d4:	f94000a5 	ldr	x5, [x5]
   2c6d8:	97ff632a 	bl	5380 <MPI_Allreduce@plt>
   2c6dc:	17fffd8b 	b	2bd08 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xb48>
   2c6e0:	f94063f6 	ldr	x22, [sp, #192]
   2c6e4:	f94073f5 	ldr	x21, [sp, #224]
   2c6e8:	d0000180 	adrp	x0, 5e000 <typeinfo name for lqcd::Error+0x9b8>
   2c6ec:	52800001 	mov	w1, #0x0                   	// #0
   2c6f0:	9101e000 	add	x0, x0, #0x78
   2c6f4:	cb1602a2 	sub	x2, x21, x22
   2c6f8:	f9006be2 	str	x2, [sp, #208]
   2c6fc:	97ff833d 	bl	d3f0 <lqcd_native::detail::setting(char const*, int)>
   2c700:	34001840 	cbz	w0, 2ca08 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1848>
   2c704:	f0000280 	adrp	x0, 7f000 <__FRAME_END__+0x18c0c>
   2c708:	f947c800 	ldr	x0, [x0, #3984]
   2c70c:	b9400000 	ldr	w0, [x0]
   2c710:	350017c0 	cbnz	w0, 2ca08 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1848>
   2c714:	f0000293 	adrp	x19, 7f000 <__FRAME_END__+0x18c0c>
   2c718:	d0000181 	adrp	x1, 5e000 <typeinfo name for lqcd::Error+0x9b8>
   2c71c:	cb1602a3 	sub	x3, x21, x22
   2c720:	f947de60 	ldr	x0, [x19, #4024]
   2c724:	d2800462 	mov	x2, #0x23                  	// #35
   2c728:	91022021 	add	x1, x1, #0x88
   2c72c:	f9006be3 	str	x3, [sp, #208]
   2c730:	97ff62f8 	bl	5310 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2c734:	f947de60 	ldr	x0, [x19, #4024]
   2c738:	b94097e1 	ldr	w1, [sp, #148]
   2c73c:	cb1602a2 	sub	x2, x21, x22
   2c740:	f9006be2 	str	x2, [sp, #208]
   2c744:	97ff63eb 	bl	56f0 <std::ostream::operator<<(int)@plt>
   2c748:	d0000181 	adrp	x1, 5e000 <typeinfo name for lqcd::Error+0x9b8>
   2c74c:	cb1602a3 	sub	x3, x21, x22
   2c750:	d2800262 	mov	x2, #0x13                  	// #19
   2c754:	9102c021 	add	x1, x1, #0xb0
   2c758:	aa0003f4 	mov	x20, x0
   2c75c:	f9006be3 	str	x3, [sp, #208]
   2c760:	97ff62ec 	bl	5310 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2c764:	b94b6381 	ldr	w1, [x28, #2912]
   2c768:	cb1602a2 	sub	x2, x21, x22
   2c76c:	aa1403e0 	mov	x0, x20
   2c770:	f9006be2 	str	x2, [sp, #208]
   2c774:	97ff63df 	bl	56f0 <std::ostream::operator<<(int)@plt>
   2c778:	d0000181 	adrp	x1, 5e000 <typeinfo name for lqcd::Error+0x9b8>
   2c77c:	cb1602a3 	sub	x3, x21, x22
   2c780:	d2800282 	mov	x2, #0x14                  	// #20
   2c784:	91032021 	add	x1, x1, #0xc8
   2c788:	aa0003f4 	mov	x20, x0
   2c78c:	f9006be3 	str	x3, [sp, #208]
   2c790:	97ff62e0 	bl	5310 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2c794:	fd452b80 	ldr	d0, [x28, #2640]
   2c798:	cb1602a1 	sub	x1, x21, x22
   2c79c:	aa1403e0 	mov	x0, x20
   2c7a0:	f9006be1 	str	x1, [sp, #208]
   2c7a4:	97ff639f 	bl	5620 <std::ostream& std::ostream::_M_insert<double>(double)@plt>
   2c7a8:	d0000181 	adrp	x1, 5e000 <typeinfo name for lqcd::Error+0x9b8>
   2c7ac:	cb1602a3 	sub	x3, x21, x22
   2c7b0:	d2800282 	mov	x2, #0x14                  	// #20
   2c7b4:	91038021 	add	x1, x1, #0xe0
   2c7b8:	aa0003f4 	mov	x20, x0
   2c7bc:	f9006be3 	str	x3, [sp, #208]
   2c7c0:	97ff62d4 	bl	5310 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2c7c4:	b940fbf7 	ldr	w23, [sp, #248]
   2c7c8:	cb1602a2 	sub	x2, x21, x22
   2c7cc:	aa1403e0 	mov	x0, x20
   2c7d0:	f9006be2 	str	x2, [sp, #208]
   2c7d4:	2a1703e1 	mov	w1, w23
   2c7d8:	97ff63c6 	bl	56f0 <std::ostream::operator<<(int)@plt>
   2c7dc:	d0000181 	adrp	x1, 5e000 <typeinfo name for lqcd::Error+0x9b8>
   2c7e0:	cb1602a3 	sub	x3, x21, x22
   2c7e4:	d2800262 	mov	x2, #0x13                  	// #19
   2c7e8:	9103e021 	add	x1, x1, #0xf8
   2c7ec:	aa0003f4 	mov	x20, x0
   2c7f0:	f9006be3 	str	x3, [sp, #208]
   2c7f4:	97ff62c7 	bl	5310 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2c7f8:	f94057e0 	ldr	x0, [sp, #168]
   2c7fc:	cb1602a2 	sub	x2, x21, x22
   2c800:	f9006be2 	str	x2, [sp, #208]
   2c804:	f9475801 	ldr	x1, [x0, #3760]
   2c808:	aa1403e0 	mov	x0, x20
   2c80c:	b9400021 	ldr	w1, [x1]
   2c810:	7100043f 	cmp	w1, #0x1
   2c814:	1a9fc2e1 	csel	w1, w23, wzr, gt
   2c818:	97ff63b6 	bl	56f0 <std::ostream::operator<<(int)@plt>
   2c81c:	900002a0 	adrp	x0, 80000 <std::ostream::put(char)@GLIBCXX_3.4>
   2c820:	d000019a 	adrp	x26, 5e000 <typeinfo name for lqcd::Error+0x9b8>
   2c824:	9106c3e1 	add	x1, sp, #0x1b0
   2c828:	9117e000 	add	x0, x0, #0x5f8
   2c82c:	d0000197 	adrp	x23, 5e000 <typeinfo name for lqcd::Error+0x9b8>
   2c830:	aa0103f8 	mov	x24, x1
   2c834:	4c40a000 	ld1	{v0.16b, v1.16b}, [x0]
   2c838:	91046340 	add	x0, x26, #0x118
   2c83c:	910482f7 	add	x23, x23, #0x120
   2c840:	52800016 	mov	w22, #0x0                   	// #0
   2c844:	d0000199 	adrp	x25, 5e000 <typeinfo name for lqcd::Error+0x9b8>
   2c848:	f9004fe0 	str	x0, [sp, #152]
   2c84c:	4c00a020 	st1	{v0.16b, v1.16b}, [x1]
   2c850:	f94063e4 	ldr	x4, [sp, #192]
   2c854:	f94073e3 	ldr	x3, [sp, #224]
   2c858:	d2800042 	mov	x2, #0x2                   	// #2
   2c85c:	91044321 	add	x1, x25, #0x110
   2c860:	f947de60 	ldr	x0, [x19, #4024]
   2c864:	cb040063 	sub	x3, x3, x4
   2c868:	f9006be3 	str	x3, [sp, #208]
   2c86c:	97ff62a9 	bl	5310 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2c870:	f9400314 	ldr	x20, [x24]
   2c874:	b4002514 	cbz	x20, 2cd14 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1b54>
   2c878:	f94063e2 	ldr	x2, [sp, #192]
   2c87c:	f94073e1 	ldr	x1, [sp, #224]
   2c880:	aa1403e0 	mov	x0, x20
   2c884:	cb020021 	sub	x1, x1, x2
   2c888:	f9006be1 	str	x1, [sp, #208]
   2c88c:	97ff61c1 	bl	4f90 <strlen@plt>
   2c890:	aa0003e2 	mov	x2, x0
   2c894:	f947de60 	ldr	x0, [x19, #4024]
   2c898:	aa1403e1 	mov	x1, x20
   2c89c:	97ff629d 	bl	5310 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2c8a0:	f94063e4 	ldr	x4, [sp, #192]
   2c8a4:	f94073e3 	ldr	x3, [sp, #224]
   2c8a8:	d2800062 	mov	x2, #0x3                   	// #3
   2c8ac:	f947de60 	ldr	x0, [x19, #4024]
   2c8b0:	f9404fe1 	ldr	x1, [sp, #152]
   2c8b4:	cb040063 	sub	x3, x3, x4
   2c8b8:	f9006be3 	str	x3, [sp, #208]
   2c8bc:	97ff6295 	bl	5310 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2c8c0:	d0000180 	adrp	x0, 5e000 <typeinfo name for lqcd::Error+0x9b8>
   2c8c4:	52800014 	mov	w20, #0x0                   	// #0
   2c8c8:	d2800015 	mov	x21, #0x0                   	// #0
   2c8cc:	91134000 	add	x0, x0, #0x4d0
   2c8d0:	f90047e0 	str	x0, [sp, #136]
   2c8d4:	34001636 	cbz	w22, 2cb98 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x19d8>
   2c8d8:	710006df 	cmp	w22, #0x1
   2c8dc:	54001940 	b.eq	2cc04 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1a44>  // b.none
   2c8e0:	71000adf 	cmp	w22, #0x2
   2c8e4:	54001c60 	b.eq	2cc70 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1ab0>  // b.none
   2c8e8:	f940b3e0 	ldr	x0, [sp, #352]
   2c8ec:	8b150000 	add	x0, x0, x21
   2c8f0:	39431001 	ldrb	w1, [x0, #196]
   2c8f4:	35001f61 	cbnz	w1, 2cce0 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1b20>
   2c8f8:	b940b801 	ldr	w1, [x0, #184]
   2c8fc:	b94b6382 	ldr	w2, [x28, #2912]
   2c900:	5280001a 	mov	w26, #0x0                   	// #0
   2c904:	6b01005f 	cmp	w2, w1
   2c908:	54001c20 	b.eq	2cc8c <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1acc>  // b.none
   2c90c:	34001cd4 	cbz	w20, 2cca4 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1ae4>
   2c910:	d2800022 	mov	x2, #0x1                   	// #1
   2c914:	aa1703e1 	mov	x1, x23
   2c918:	f94063e4 	ldr	x4, [sp, #192]
   2c91c:	f94073e3 	ldr	x3, [sp, #224]
   2c920:	f947de60 	ldr	x0, [x19, #4024]
   2c924:	cb040065 	sub	x5, x3, x4
   2c928:	f9006be5 	str	x5, [sp, #208]
   2c92c:	97ff6279 	bl	5310 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2c930:	f94063e4 	ldr	x4, [sp, #192]
   2c934:	f94073e2 	ldr	x2, [sp, #224]
   2c938:	2a1a03e1 	mov	w1, w26
   2c93c:	f947de60 	ldr	x0, [x19, #4024]
   2c940:	cb040042 	sub	x2, x2, x4
   2c944:	f9006be2 	str	x2, [sp, #208]
   2c948:	97ff636a 	bl	56f0 <std::ostream::operator<<(int)@plt>
   2c94c:	b94097e0 	ldr	w0, [sp, #148]
   2c950:	11000694 	add	w20, w20, #0x1
   2c954:	910322b5 	add	x21, x21, #0xc8
   2c958:	6b14001f 	cmp	w0, w20
   2c95c:	54fffc6c 	b.gt	2c8e8 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1728>
   2c960:	52800ba3 	mov	w3, #0x5d                  	// #93
   2c964:	f94063e4 	ldr	x4, [sp, #192]
   2c968:	f947de60 	ldr	x0, [x19, #4024]
   2c96c:	d2800022 	mov	x2, #0x1                   	// #1
   2c970:	39056fe3 	strb	w3, [sp, #347]
   2c974:	f94073e3 	ldr	x3, [sp, #224]
   2c978:	91056fe1 	add	x1, sp, #0x15b
   2c97c:	cb040063 	sub	x3, x3, x4
   2c980:	f9006be3 	str	x3, [sp, #208]
   2c984:	97ff6263 	bl	5310 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2c988:	110006d6 	add	w22, w22, #0x1
   2c98c:	91002318 	add	x24, x24, #0x8
   2c990:	710012df 	cmp	w22, #0x4
   2c994:	54fff5e1 	b.ne	2c850 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1690>  // b.any
   2c998:	f94063e5 	ldr	x5, [sp, #192]
   2c99c:	f94073e4 	ldr	x4, [sp, #224]
   2c9a0:	52800fa3 	mov	w3, #0x7d                  	// #125
   2c9a4:	d2800022 	mov	x2, #0x1                   	// #1
   2c9a8:	f947de60 	ldr	x0, [x19, #4024]
   2c9ac:	910573e1 	add	x1, sp, #0x15c
   2c9b0:	390573e3 	strb	w3, [sp, #348]
   2c9b4:	cb050084 	sub	x4, x4, x5
   2c9b8:	f9006be4 	str	x4, [sp, #208]
   2c9bc:	97ff6255 	bl	5310 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2c9c0:	aa0003f4 	mov	x20, x0
   2c9c4:	f9400000 	ldr	x0, [x0]
   2c9c8:	f85e8000 	ldur	x0, [x0, #-24]
   2c9cc:	8b000280 	add	x0, x20, x0
   2c9d0:	f9407813 	ldr	x19, [x0, #240]
   2c9d4:	b4002453 	cbz	x19, 2ce5c <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1c9c>
   2c9d8:	3940e260 	ldrb	w0, [x19, #56]
   2c9dc:	34001c40 	cbz	w0, 2cd64 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1ba4>
   2c9e0:	39410e61 	ldrb	w1, [x19, #67]
   2c9e4:	aa1403e0 	mov	x0, x20
   2c9e8:	f94063f4 	ldr	x20, [sp, #192]
   2c9ec:	f94073f3 	ldr	x19, [sp, #224]
   2c9f0:	cb140262 	sub	x2, x19, x20
   2c9f4:	f9006be2 	str	x2, [sp, #208]
   2c9f8:	97ff6126 	bl	4e90 <std::ostream::put(char)@plt>
   2c9fc:	cb140261 	sub	x1, x19, x20
   2ca00:	f9006be1 	str	x1, [sp, #208]
   2ca04:	97ff61db 	bl	5170 <std::ostream::flush()@plt>
   2ca08:	f94063e0 	ldr	x0, [sp, #192]
   2ca0c:	b4000080 	cbz	x0, 2ca1c <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x185c>
   2ca10:	f94073e1 	ldr	x1, [sp, #224]
   2ca14:	cb000021 	sub	x1, x1, x0
   2ca18:	97ff6216 	bl	5270 <operator delete(void*, unsigned long)@plt>
   2ca1c:	b40000bb 	cbz	x27, 2ca30 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1870>
   2ca20:	f9409fe0 	ldr	x0, [sp, #312]
   2ca24:	cb1b0001 	sub	x1, x0, x27
   2ca28:	aa1b03e0 	mov	x0, x27
   2ca2c:	97ff6211 	bl	5270 <operator delete(void*, unsigned long)@plt>
   2ca30:	f940cbe0 	ldr	x0, [sp, #400]
   2ca34:	b4000080 	cbz	x0, 2ca44 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1884>
   2ca38:	f940d3e1 	ldr	x1, [sp, #416]
   2ca3c:	cb000021 	sub	x1, x1, x0
   2ca40:	97ff620c 	bl	5270 <operator delete(void*, unsigned long)@plt>
   2ca44:	f940bfe0 	ldr	x0, [sp, #376]
   2ca48:	b4000080 	cbz	x0, 2ca58 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1898>
   2ca4c:	f940c7e1 	ldr	x1, [sp, #392]
   2ca50:	cb000021 	sub	x1, x1, x0
   2ca54:	97ff6207 	bl	5270 <operator delete(void*, unsigned long)@plt>
   2ca58:	f94053e0 	ldr	x0, [sp, #160]
   2ca5c:	f94087e1 	ldr	x1, [sp, #264]
   2ca60:	cb000021 	sub	x1, x1, x0
   2ca64:	97ff6203 	bl	5270 <operator delete(void*, unsigned long)@plt>
   2ca68:	a9565bf5 	ldp	x21, x22, [sp, #352]
   2ca6c:	eb1602bf 	cmp	x21, x22
   2ca70:	54ffc060 	b.eq	2c27c <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x10bc>  // b.none
   2ca74:	d503201f 	nop
   2ca78:	a94952b3 	ldp	x19, x20, [x21, #144]
   2ca7c:	eb14027f 	cmp	x19, x20
   2ca80:	54000120 	b.eq	2caa4 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x18e4>  // b.none
   2ca84:	d503201f 	nop
   2ca88:	f9400260 	ldr	x0, [x19]
   2ca8c:	91006273 	add	x19, x19, #0x18
   2ca90:	b4001180 	cbz	x0, 2ccc0 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1b00>
   2ca94:	97ff6183 	bl	50a0 <free@plt>
   2ca98:	eb14027f 	cmp	x19, x20
   2ca9c:	54ffff61 	b.ne	2ca88 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x18c8>  // b.any
   2caa0:	f9404ab4 	ldr	x20, [x21, #144]
   2caa4:	b40000b4 	cbz	x20, 2cab8 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x18f8>
   2caa8:	f94052a1 	ldr	x1, [x21, #160]
   2caac:	aa1403e0 	mov	x0, x20
   2cab0:	cb140021 	sub	x1, x1, x20
   2cab4:	97ff61ef 	bl	5270 <operator delete(void*, unsigned long)@plt>
   2cab8:	a947d2b3 	ldp	x19, x20, [x21, #120]
   2cabc:	eb14027f 	cmp	x19, x20
   2cac0:	54000120 	b.eq	2cae4 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1924>  // b.none
   2cac4:	d503201f 	nop
   2cac8:	f9400260 	ldr	x0, [x19]
   2cacc:	91006273 	add	x19, x19, #0x18
   2cad0:	b4000f00 	cbz	x0, 2ccb0 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1af0>
   2cad4:	97ff6173 	bl	50a0 <free@plt>
   2cad8:	eb14027f 	cmp	x19, x20
   2cadc:	54ffff61 	b.ne	2cac8 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1908>  // b.any
   2cae0:	f9403eb4 	ldr	x20, [x21, #120]
   2cae4:	b40000b4 	cbz	x20, 2caf8 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1938>
   2cae8:	f94046a1 	ldr	x1, [x21, #136]
   2caec:	aa1403e0 	mov	x0, x20
   2caf0:	cb140021 	sub	x1, x1, x20
   2caf4:	97ff61df 	bl	5270 <operator delete(void*, unsigned long)@plt>
   2caf8:	f94032a0 	ldr	x0, [x21, #96]
   2cafc:	b4000040 	cbz	x0, 2cb04 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1944>
   2cb00:	97ff6168 	bl	50a0 <free@plt>
   2cb04:	f94026a0 	ldr	x0, [x21, #72]
   2cb08:	b4000040 	cbz	x0, 2cb10 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1950>
   2cb0c:	97ff6165 	bl	50a0 <free@plt>
   2cb10:	f9401aa0 	ldr	x0, [x21, #48]
   2cb14:	b4000040 	cbz	x0, 2cb1c <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x195c>
   2cb18:	97ff6162 	bl	50a0 <free@plt>
   2cb1c:	f9400ea0 	ldr	x0, [x21, #24]
   2cb20:	b4000040 	cbz	x0, 2cb28 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1968>
   2cb24:	97ff615f 	bl	50a0 <free@plt>
   2cb28:	f94002a0 	ldr	x0, [x21]
   2cb2c:	910322b5 	add	x21, x21, #0xc8
   2cb30:	b4000d00 	cbz	x0, 2ccd0 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1b10>
   2cb34:	97ff615b 	bl	50a0 <free@plt>
   2cb38:	eb1502df 	cmp	x22, x21
   2cb3c:	54fff9e1 	b.ne	2ca78 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x18b8>  // b.any
   2cb40:	f940b3f6 	ldr	x22, [sp, #352]
   2cb44:	17fffdce 	b	2c27c <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x10bc>
   2cb48:	d2800022 	mov	x2, #0x1                   	// #1
   2cb4c:	aa1703e1 	mov	x1, x23
   2cb50:	f94063e4 	ldr	x4, [sp, #192]
   2cb54:	f94073e3 	ldr	x3, [sp, #224]
   2cb58:	f947de60 	ldr	x0, [x19, #4024]
   2cb5c:	cb040063 	sub	x3, x3, x4
   2cb60:	f9006be3 	str	x3, [sp, #208]
   2cb64:	97ff61eb 	bl	5310 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2cb68:	f94063e3 	ldr	x3, [sp, #192]
   2cb6c:	f94073e2 	ldr	x2, [sp, #224]
   2cb70:	2a1a03e1 	mov	w1, w26
   2cb74:	f947de60 	ldr	x0, [x19, #4024]
   2cb78:	cb030042 	sub	x2, x2, x3
   2cb7c:	f9006be2 	str	x2, [sp, #208]
   2cb80:	97ff62dc 	bl	56f0 <std::ostream::operator<<(int)@plt>
   2cb84:	b94097e0 	ldr	w0, [sp, #148]
   2cb88:	11000694 	add	w20, w20, #0x1
   2cb8c:	910322b5 	add	x21, x21, #0xc8
   2cb90:	6b00029f 	cmp	w20, w0
   2cb94:	54ffee6a 	b.ge	2c960 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x17a0>  // b.tcont
   2cb98:	f940b3e0 	ldr	x0, [sp, #352]
   2cb9c:	8b150000 	add	x0, x0, x21
   2cba0:	b940b81a 	ldr	w26, [x0, #184]
   2cba4:	35fffd34 	cbnz	w20, 2cb48 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1988>
   2cba8:	d2800002 	mov	x2, #0x0                   	// #0
   2cbac:	f94047e1 	ldr	x1, [sp, #136]
   2cbb0:	17ffffe8 	b	2cb50 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1990>
   2cbb4:	f94047e1 	ldr	x1, [sp, #136]
   2cbb8:	d2800002 	mov	x2, #0x0                   	// #0
   2cbbc:	f94063e4 	ldr	x4, [sp, #192]
   2cbc0:	f94073e3 	ldr	x3, [sp, #224]
   2cbc4:	f947de60 	ldr	x0, [x19, #4024]
   2cbc8:	cb040065 	sub	x5, x3, x4
   2cbcc:	f9006be5 	str	x5, [sp, #208]
   2cbd0:	97ff61d0 	bl	5310 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2cbd4:	f94063e4 	ldr	x4, [sp, #192]
   2cbd8:	f94073e2 	ldr	x2, [sp, #224]
   2cbdc:	2a1a03e1 	mov	w1, w26
   2cbe0:	f947de60 	ldr	x0, [x19, #4024]
   2cbe4:	cb040042 	sub	x2, x2, x4
   2cbe8:	f9006be2 	str	x2, [sp, #208]
   2cbec:	97ff62c1 	bl	56f0 <std::ostream::operator<<(int)@plt>
   2cbf0:	b94097e0 	ldr	w0, [sp, #148]
   2cbf4:	11000694 	add	w20, w20, #0x1
   2cbf8:	910322b5 	add	x21, x21, #0xc8
   2cbfc:	6b14001f 	cmp	w0, w20
   2cc00:	54ffeb0d 	b.le	2c960 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x17a0>
   2cc04:	f940b3e0 	ldr	x0, [sp, #352]
   2cc08:	8b150000 	add	x0, x0, x21
   2cc0c:	b940bc1a 	ldr	w26, [x0, #188]
   2cc10:	34fffd34 	cbz	w20, 2cbb4 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x19f4>
   2cc14:	d2800022 	mov	x2, #0x1                   	// #1
   2cc18:	aa1703e1 	mov	x1, x23
   2cc1c:	17ffffe8 	b	2cbbc <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x19fc>
   2cc20:	f94047e1 	ldr	x1, [sp, #136]
   2cc24:	d2800002 	mov	x2, #0x0                   	// #0
   2cc28:	f94063e4 	ldr	x4, [sp, #192]
   2cc2c:	f94073e3 	ldr	x3, [sp, #224]
   2cc30:	f947de60 	ldr	x0, [x19, #4024]
   2cc34:	cb040065 	sub	x5, x3, x4
   2cc38:	f9006be5 	str	x5, [sp, #208]
   2cc3c:	97ff61b5 	bl	5310 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2cc40:	f94063e4 	ldr	x4, [sp, #192]
   2cc44:	f94073e2 	ldr	x2, [sp, #224]
   2cc48:	2a1a03e1 	mov	w1, w26
   2cc4c:	f947de60 	ldr	x0, [x19, #4024]
   2cc50:	cb040042 	sub	x2, x2, x4
   2cc54:	f9006be2 	str	x2, [sp, #208]
   2cc58:	97ff62a6 	bl	56f0 <std::ostream::operator<<(int)@plt>
   2cc5c:	b94097e0 	ldr	w0, [sp, #148]
   2cc60:	11000694 	add	w20, w20, #0x1
   2cc64:	910322b5 	add	x21, x21, #0xc8
   2cc68:	6b14001f 	cmp	w0, w20
   2cc6c:	54ffe7ad 	b.le	2c960 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x17a0>
   2cc70:	f940b3e0 	ldr	x0, [sp, #352]
   2cc74:	8b150000 	add	x0, x0, x21
   2cc78:	b940c01a 	ldr	w26, [x0, #192]
   2cc7c:	34fffd34 	cbz	w20, 2cc20 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1a60>
   2cc80:	d2800022 	mov	x2, #0x1                   	// #1
   2cc84:	aa1703e1 	mov	x1, x23
   2cc88:	17ffffe8 	b	2cc28 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1a68>
   2cc8c:	6d4a8400 	ldp	d0, d1, [x0, #168]
   2cc90:	fd452b82 	ldr	d2, [x28, #2640]
   2cc94:	1e620800 	fmul	d0, d0, d2
   2cc98:	1e612010 	fcmpe	d0, d1
   2cc9c:	1a9f87fa 	cset	w26, ls  // ls = plast
   2cca0:	35ffe394 	cbnz	w20, 2c910 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1750>
   2cca4:	d2800002 	mov	x2, #0x0                   	// #0
   2cca8:	f94047e1 	ldr	x1, [sp, #136]
   2ccac:	17ffff1b 	b	2c918 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1758>
   2ccb0:	eb13029f 	cmp	x20, x19
   2ccb4:	54fff0a1 	b.ne	2cac8 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1908>  // b.any
   2ccb8:	f9403eb4 	ldr	x20, [x21, #120]
   2ccbc:	17ffff8a 	b	2cae4 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1924>
   2ccc0:	eb13029f 	cmp	x20, x19
   2ccc4:	54ffee21 	b.ne	2ca88 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x18c8>  // b.any
   2ccc8:	f9404ab4 	ldr	x20, [x21, #144]
   2cccc:	17ffff76 	b	2caa4 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x18e4>
   2ccd0:	eb1502df 	cmp	x22, x21
   2ccd4:	54ffed21 	b.ne	2ca78 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x18b8>  // b.any
   2ccd8:	f940b3f6 	ldr	x22, [sp, #352]
   2ccdc:	17fffd68 	b	2c27c <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x10bc>
   2cce0:	5280001a 	mov	w26, #0x0                   	// #0
   2cce4:	17ffff0a 	b	2c90c <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x174c>
   2cce8:	eb1402df 	cmp	x22, x20
   2ccec:	54ffa621 	b.ne	2c1b0 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xff0>  // b.any
   2ccf0:	f940b3f6 	ldr	x22, [sp, #352]
   2ccf4:	17fffd62 	b	2c27c <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x10bc>
   2ccf8:	5280001b 	mov	w27, #0x0                   	// #0
   2ccfc:	17fffcfc 	b	2c0ec <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xf2c>
   2cd00:	d2800002 	mov	x2, #0x0                   	// #0
   2cd04:	f94047e1 	ldr	x1, [sp, #136]
   2cd08:	17fffcfc 	b	2c0f8 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xf38>
   2cd0c:	f940b3fa 	ldr	x26, [sp, #352]
   2cd10:	17fffc38 	b	2bdf0 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xc30>
   2cd14:	f94063e2 	ldr	x2, [sp, #192]
   2cd18:	f94073e0 	ldr	x0, [sp, #224]
   2cd1c:	f947de61 	ldr	x1, [x19, #4024]
   2cd20:	cb020000 	sub	x0, x0, x2
   2cd24:	f9006be0 	str	x0, [sp, #208]
   2cd28:	f9400020 	ldr	x0, [x1]
   2cd2c:	f85e8000 	ldur	x0, [x0, #-24]
   2cd30:	8b010000 	add	x0, x0, x1
   2cd34:	b9402001 	ldr	w1, [x0, #32]
   2cd38:	32000021 	orr	w1, w1, #0x1
   2cd3c:	97ff6261 	bl	56c0 <std::basic_ios<char, std::char_traits<char> >::clear(std::_Ios_Iostate)@plt>
   2cd40:	17fffed8 	b	2c8a0 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x16e0>
   2cd44:	f90063ff 	str	xzr, [sp, #192]
   2cd48:	f90073ff 	str	xzr, [sp, #224]
   2cd4c:	17fffa69 	b	2b6f0 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x530>
   2cd50:	f94063e0 	ldr	x0, [sp, #192]
   2cd54:	f94073e1 	ldr	x1, [sp, #224]
   2cd58:	eb01001f 	cmp	x0, x1
   2cd5c:	54ff6121 	b.ne	2b980 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x7c0>  // b.any
   2cd60:	17fffb0e 	b	2b998 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x7d8>
   2cd64:	f94063e2 	ldr	x2, [sp, #192]
   2cd68:	f94073e1 	ldr	x1, [sp, #224]
   2cd6c:	aa1303e0 	mov	x0, x19
   2cd70:	cb020021 	sub	x1, x1, x2
   2cd74:	f9006be1 	str	x1, [sp, #208]
   2cd78:	97ff616a 	bl	5320 <std::ctype<char>::_M_widen_init() const@plt>
   2cd7c:	f9400262 	ldr	x2, [x19]
   2cd80:	b0ffffe0 	adrp	x0, 29000 <NativeMG::Impl::coarse_solve_eo(std::vector<float, lqcd_native::WorkspaceAllocator<float> > const&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&) const+0x7c0>
   2cd84:	52800141 	mov	w1, #0xa                   	// #10
   2cd88:	9130c000 	add	x0, x0, #0xc30
   2cd8c:	f9401842 	ldr	x2, [x2, #48]
   2cd90:	eb00005f 	cmp	x2, x0
   2cd94:	54ffe280 	b.eq	2c9e4 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1824>  // b.none
   2cd98:	f94063e4 	ldr	x4, [sp, #192]
   2cd9c:	f94073e3 	ldr	x3, [sp, #224]
   2cda0:	aa1303e0 	mov	x0, x19
   2cda4:	cb040063 	sub	x3, x3, x4
   2cda8:	f9006be3 	str	x3, [sp, #208]
   2cdac:	d63f0040 	blr	x2
   2cdb0:	12001c01 	and	w1, w0, #0xff
   2cdb4:	17ffff0c 	b	2c9e4 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1824>
   2cdb8:	f947de61 	ldr	x1, [x19, #4024]
   2cdbc:	f9400020 	ldr	x0, [x1]
   2cdc0:	f85e8000 	ldur	x0, [x0, #-24]
   2cdc4:	8b010000 	add	x0, x0, x1
   2cdc8:	b9402001 	ldr	w1, [x0, #32]
   2cdcc:	32000021 	orr	w1, w1, #0x1
   2cdd0:	97ff623c 	bl	56c0 <std::basic_ios<char, std::char_traits<char> >::clear(std::_Ios_Iostate)@plt>
   2cdd4:	17fffcac 	b	2c084 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xec4>
   2cdd8:	52800040 	mov	w0, #0x2                   	// #2
   2cddc:	b900fbe0 	str	w0, [sp, #248]
   2cde0:	17fffc04 	b	2bdf0 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xc30>
   2cde4:	aa1303e0 	mov	x0, x19
   2cde8:	97ff614e 	bl	5320 <std::ctype<char>::_M_widen_init() const@plt>
   2cdec:	f9400262 	ldr	x2, [x19]
   2cdf0:	b0ffffe0 	adrp	x0, 29000 <NativeMG::Impl::coarse_solve_eo(std::vector<float, lqcd_native::WorkspaceAllocator<float> > const&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&) const+0x7c0>
   2cdf4:	52800141 	mov	w1, #0xa                   	// #10
   2cdf8:	9130c000 	add	x0, x0, #0xc30
   2cdfc:	f9401842 	ldr	x2, [x2, #48]
   2ce00:	eb00005f 	cmp	x2, x0
   2ce04:	54ff9c00 	b.eq	2c184 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xfc4>  // b.none
   2ce08:	aa1303e0 	mov	x0, x19
   2ce0c:	d63f0040 	blr	x2
   2ce10:	12001c01 	and	w1, w0, #0xff
   2ce14:	17fffcdc 	b	2c184 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xfc4>
   2ce18:	f9005be3 	str	x3, [sp, #176]
   2ce1c:	17fffa23 	b	2b6a8 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x4e8>
   2ce20:	b0000180 	adrp	x0, 5d000 <_fini+0x34>
   2ce24:	9117c000 	add	x0, x0, #0x5f0
   2ce28:	97ff6092 	bl	5070 <std::__throw_length_error(char const*)@plt>
   2ce2c:	f94087e0 	ldr	x0, [sp, #264]
   2ce30:	f9007be0 	str	x0, [sp, #240]
   2ce34:	17fffc30 	b	2bef4 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xd34>
   2ce38:	97ff6162 	bl	53c0 <std::__throw_bad_cast()@plt>
   2ce3c:	b0000180 	adrp	x0, 5d000 <_fini+0x34>
   2ce40:	9117c000 	add	x0, x0, #0x5f0
   2ce44:	97ff608b 	bl	5070 <std::__throw_length_error(char const*)@plt>
   2ce48:	1e61c000 	fsqrt	d0, d0
   2ce4c:	17fffb25 	b	2bae0 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x920>
   2ce50:	b0000180 	adrp	x0, 5d000 <_fini+0x34>
   2ce54:	9117c000 	add	x0, x0, #0x5f0
   2ce58:	97ff6086 	bl	5070 <std::__throw_length_error(char const*)@plt>
   2ce5c:	f94063e1 	ldr	x1, [sp, #192]
   2ce60:	f94073e0 	ldr	x0, [sp, #224]
   2ce64:	cb010000 	sub	x0, x0, x1
   2ce68:	f9006be0 	str	x0, [sp, #208]
   2ce6c:	97ff6155 	bl	53c0 <std::__throw_bad_cast()@plt>
   2ce70:	aa1403e1 	mov	x1, x20
   2ce74:	aa0003f3 	mov	x19, x0
   2ce78:	aa1b03e0 	mov	x0, x27
   2ce7c:	97ff60fd 	bl	5270 <operator delete(void*, unsigned long)@plt>
   2ce80:	f940cbe0 	ldr	x0, [sp, #400]
   2ce84:	f940d3e1 	ldr	x1, [sp, #416]
   2ce88:	cb000021 	sub	x1, x1, x0
   2ce8c:	b4000040 	cbz	x0, 2ce94 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1cd4>
   2ce90:	97ff60f8 	bl	5270 <operator delete(void*, unsigned long)@plt>
   2ce94:	f940bfe0 	ldr	x0, [sp, #376]
   2ce98:	f940c7e1 	ldr	x1, [sp, #392]
   2ce9c:	cb000021 	sub	x1, x1, x0
   2cea0:	b4000040 	cbz	x0, 2cea8 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1ce8>
   2cea4:	97ff60f3 	bl	5270 <operator delete(void*, unsigned long)@plt>
   2cea8:	f94053e1 	ldr	x1, [sp, #160]
   2ceac:	f94087e0 	ldr	x0, [sp, #264]
   2ceb0:	cb010001 	sub	x1, x0, x1
   2ceb4:	f94053e0 	ldr	x0, [sp, #160]
   2ceb8:	97ff60ee 	bl	5270 <operator delete(void*, unsigned long)@plt>
   2cebc:	910583e0 	add	x0, sp, #0x160
   2cec0:	97fff7c0 	bl	2adc0 <std::vector<NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const::State, std::allocator<NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const::State> >::~vector()>
   2cec4:	b94137e0 	ldr	w0, [sp, #308]
   2cec8:	34000060 	cbz	w0, 2ced4 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1d14>
   2cecc:	b94133e0 	ldr	w0, [sp, #304]
   2ced0:	97ff6104 	bl	52e0 <omp_set_num_threads@plt>
   2ced4:	aa1303e0 	mov	x0, x19
   2ced8:	97ff6212 	bl	5720 <_Unwind_Resume@plt>
   2cedc:	aa0003f3 	mov	x19, x0
   2cee0:	17ffffe8 	b	2ce80 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1cc0>
   2cee4:	aa0003f3 	mov	x19, x0
   2cee8:	f9409fe0 	ldr	x0, [sp, #312]
   2ceec:	cb1b0001 	sub	x1, x0, x27
   2cef0:	b5fffc5b 	cbnz	x27, 2ce78 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1cb8>
   2cef4:	17ffffe3 	b	2ce80 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1cc0>
   2cef8:	aa0003f3 	mov	x19, x0
   2cefc:	17fffff0 	b	2cebc <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1cfc>
   2cf00:	f94053e2 	ldr	x2, [sp, #160]
   2cf04:	f94087e1 	ldr	x1, [sp, #264]
   2cf08:	aa0003f3 	mov	x19, x0
   2cf0c:	cb020021 	sub	x1, x1, x2
   2cf10:	b5fffd22 	cbnz	x2, 2ceb4 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1cf4>
   2cf14:	17ffffea 	b	2cebc <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1cfc>
   2cf18:	aa0003f3 	mov	x19, x0
   2cf1c:	17ffffe3 	b	2cea8 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1ce8>
   2cf20:	aa0003f3 	mov	x19, x0
   2cf24:	f94063e0 	ldr	x0, [sp, #192]
   2cf28:	b4fffe00 	cbz	x0, 2cee8 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1d28>
   2cf2c:	f9406be1 	ldr	x1, [sp, #208]
   2cf30:	97ff60d0 	bl	5270 <operator delete(void*, unsigned long)@plt>
   2cf34:	17ffffed 	b	2cee8 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1d28>
   2cf38:	aa0003f3 	mov	x19, x0
   2cf3c:	17ffffe2 	b	2cec4 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1d04>
   2cf40:	f940dbe1 	ldr	x1, [sp, #432]
   2cf44:	aa0003f3 	mov	x19, x0
   2cf48:	b4fffee1 	cbz	x1, 2cf24 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1d64>
   2cf4c:	aa0103e0 	mov	x0, x1
   2cf50:	97ff6054 	bl	50a0 <free@plt>
   2cf54:	17fffff4 	b	2cf24 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1d64>
