
/home/share/nsls_lwb/.cache/mg-opt-20261103/campaign-halo-v2/attempts/000-halo-v2-tests/build/liblqcd_cpu.so.0.2.0:     file format elf64-littleaarch64


Disassembly of section .text:

000000000002d1c0 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const>:
   2d1c0:	d10943ff 	sub	sp, sp, #0x250
   2d1c4:	a9007bfd 	stp	x29, x30, [sp]
   2d1c8:	910003fd 	mov	x29, sp
   2d1cc:	a90573fb 	stp	x27, x28, [sp, #80]
   2d1d0:	aa0003fb 	mov	x27, x0
   2d1d4:	395ec800 	ldrb	w0, [x0, #1970]
   2d1d8:	6d0627e8 	stp	d8, d9, [sp, #96]
   2d1dc:	a90153f3 	stp	x19, x20, [sp, #16]
   2d1e0:	a9025bf5 	stp	x21, x22, [sp, #32]
   2d1e4:	a90363f7 	stp	x23, x24, [sp, #48]
   2d1e8:	a9046bf9 	stp	x25, x26, [sp, #64]
   2d1ec:	fd003bea 	str	d10, [sp, #112]
   2d1f0:	a90b0be1 	stp	x1, x2, [sp, #176]
   2d1f4:	b9013fe3 	str	w3, [sp, #316]
   2d1f8:	f900abfb 	str	x27, [sp, #336]
   2d1fc:	f903df7f 	str	xzr, [x27, #1976]
   2d200:	f903e37f 	str	xzr, [x27, #1984]
   2d204:	f903e77f 	str	xzr, [x27, #1992]
   2d208:	b907d37f 	str	wzr, [x27, #2000]
   2d20c:	340000e0 	cbz	w0, 2d228 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x68>
   2d210:	7100047f 	cmp	w3, #0x1
   2d214:	540000e0 	b.eq	2d230 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x70>  // b.none
   2d218:	39590760 	ldrb	w0, [x27, #1601]
   2d21c:	34000060 	cbz	w0, 2d228 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x68>
   2d220:	3968ff75 	ldrb	w21, [x27, #2623]
   2d224:	34000b55 	cbz	w21, 2d38c <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1cc>
   2d228:	7100007f 	cmp	w3, #0x0
   2d22c:	5400020d 	b.le	2d26c <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xac>
   2d230:	a94b5bf5 	ldp	x21, x22, [sp, #176]
   2d234:	d2800013 	mov	x19, #0x0                   	// #0
   2d238:	52800014 	mov	w20, #0x0                   	// #0
   2d23c:	d503201f 	nop
   2d240:	f94002a1 	ldr	x1, [x21]
   2d244:	f94002c2 	ldr	x2, [x22]
   2d248:	aa1b03e0 	mov	x0, x27
   2d24c:	11000694 	add	w20, w20, #0x1
   2d250:	8b130021 	add	x1, x1, x19
   2d254:	8b130042 	add	x2, x2, x19
   2d258:	91006273 	add	x19, x19, #0x18
   2d25c:	97ffefb9 	bl	29140 <NativeMG::Impl::coarse_solve(std::vector<float, lqcd_native::WorkspaceAllocator<float> > const&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&) const>
   2d260:	b9413fe1 	ldr	w1, [sp, #316]
   2d264:	6b14003f 	cmp	w1, w20
   2d268:	54fffecc 	b.gt	2d240 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x80>
   2d26c:	b0000180 	adrp	x0, 5e000 <typeinfo name for lqcd::Error+0x9b8>
   2d270:	52800001 	mov	w1, #0x0                   	// #0
   2d274:	9101e000 	add	x0, x0, #0x78
   2d278:	97ff805e 	bl	d3f0 <lqcd_native::detail::setting(char const*, int)>
   2d27c:	340000a0 	cbz	w0, 2d290 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xd0>
   2d280:	d0000280 	adrp	x0, 7f000 <__FRAME_END__+0x18c0c>
   2d284:	f947c800 	ldr	x0, [x0, #3984]
   2d288:	b9400000 	ldr	w0, [x0]
   2d28c:	34000160 	cbz	w0, 2d2b8 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xf8>
   2d290:	a9407bfd 	ldp	x29, x30, [sp]
   2d294:	a94153f3 	ldp	x19, x20, [sp, #16]
   2d298:	a9425bf5 	ldp	x21, x22, [sp, #32]
   2d29c:	a94363f7 	ldp	x23, x24, [sp, #48]
   2d2a0:	a9446bf9 	ldp	x25, x26, [sp, #64]
   2d2a4:	a94573fb 	ldp	x27, x28, [sp, #80]
   2d2a8:	6d4627e8 	ldp	d8, d9, [sp, #96]
   2d2ac:	fd403bea 	ldr	d10, [sp, #112]
   2d2b0:	910943ff 	add	sp, sp, #0x250
   2d2b4:	d65f03c0 	ret
   2d2b8:	d0000293 	adrp	x19, 7f000 <__FRAME_END__+0x18c0c>
   2d2bc:	f940abf4 	ldr	x20, [sp, #336]
   2d2c0:	b0000181 	adrp	x1, 5e000 <typeinfo name for lqcd::Error+0x9b8>
   2d2c4:	d2800442 	mov	x2, #0x22                  	// #34
   2d2c8:	f947de73 	ldr	x19, [x19, #4024]
   2d2cc:	9104a021 	add	x1, x1, #0x128
   2d2d0:	911ee295 	add	x21, x20, #0x7b8
   2d2d4:	aa1303e0 	mov	x0, x19
   2d2d8:	97ff600e 	bl	5310 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2d2dc:	f943de81 	ldr	x1, [x20, #1976]
   2d2e0:	aa1303e0 	mov	x0, x19
   2d2e4:	97ff5f9f 	bl	5160 <std::ostream& std::ostream::_M_insert<unsigned long>(unsigned long)@plt>
   2d2e8:	aa0003f3 	mov	x19, x0
   2d2ec:	b0000181 	adrp	x1, 5e000 <typeinfo name for lqcd::Error+0x9b8>
   2d2f0:	d28001c2 	mov	x2, #0xe                   	// #14
   2d2f4:	91054021 	add	x1, x1, #0x150
   2d2f8:	97ff6006 	bl	5310 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2d2fc:	f94006a1 	ldr	x1, [x21, #8]
   2d300:	aa1303e0 	mov	x0, x19
   2d304:	97ff5f97 	bl	5160 <std::ostream& std::ostream::_M_insert<unsigned long>(unsigned long)@plt>
   2d308:	aa0003f3 	mov	x19, x0
   2d30c:	b0000181 	adrp	x1, 5e000 <typeinfo name for lqcd::Error+0x9b8>
   2d310:	d28001a2 	mov	x2, #0xd                   	// #13
   2d314:	91058021 	add	x1, x1, #0x160
   2d318:	97ff5ffe 	bl	5310 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2d31c:	f9400aa1 	ldr	x1, [x21, #16]
   2d320:	aa1303e0 	mov	x0, x19
   2d324:	97ff5f8f 	bl	5160 <std::ostream& std::ostream::_M_insert<unsigned long>(unsigned long)@plt>
   2d328:	aa0003f3 	mov	x19, x0
   2d32c:	b0000181 	adrp	x1, 5e000 <typeinfo name for lqcd::Error+0x9b8>
   2d330:	d28001a2 	mov	x2, #0xd                   	// #13
   2d334:	9105c021 	add	x1, x1, #0x170
   2d338:	97ff5ff6 	bl	5310 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2d33c:	b9401aa1 	ldr	w1, [x21, #24]
   2d340:	aa1303e0 	mov	x0, x19
   2d344:	97ff60eb 	bl	56f0 <std::ostream::operator<<(int)@plt>
   2d348:	aa0003f3 	mov	x19, x0
   2d34c:	b0000181 	adrp	x1, 5e000 <typeinfo name for lqcd::Error+0x9b8>
   2d350:	d2800442 	mov	x2, #0x22                  	// #34
   2d354:	91060021 	add	x1, x1, #0x180
   2d358:	97ff5fee 	bl	5310 <std::basic_ostream<char, std::char_traits<char> >& std::__ostream_insert<char, std::char_traits<char> >(std::basic_ostream<char, std::char_traits<char> >&, char const*, long)@plt>
   2d35c:	f9400260 	ldr	x0, [x19]
   2d360:	f85e8000 	ldur	x0, [x0, #-24]
   2d364:	8b000260 	add	x0, x19, x0
   2d368:	f9407814 	ldr	x20, [x0, #240]
   2d36c:	b400d4b4 	cbz	x20, 2ee00 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1c40>
   2d370:	3940e280 	ldrb	w0, [x20, #56]
   2d374:	340001a0 	cbz	w0, 2d3a8 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1e8>
   2d378:	39410e81 	ldrb	w1, [x20, #67]
   2d37c:	aa1303e0 	mov	x0, x19
   2d380:	97ff5ec4 	bl	4e90 <std::ostream::put(char)@plt>
   2d384:	97ff5f7b 	bl	5170 <std::ostream::flush()@plt>
   2d388:	17ffffc2 	b	2d290 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xd0>
   2d38c:	90000180 	adrp	x0, 5d000 <_fini+0x34>
   2d390:	52800021 	mov	w1, #0x1                   	// #1
   2d394:	91258000 	add	x0, x0, #0x960
   2d398:	97ff8016 	bl	d3f0 <lqcd_native::detail::setting(char const*, int)>
   2d39c:	35000200 	cbnz	w0, 2d3dc <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x21c>
   2d3a0:	b9413fe3 	ldr	w3, [sp, #316]
   2d3a4:	17ffffa1 	b	2d228 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x68>
   2d3a8:	aa1403e0 	mov	x0, x20
   2d3ac:	97ff5fdd 	bl	5320 <std::ctype<char>::_M_widen_init() const@plt>
   2d3b0:	f9400282 	ldr	x2, [x20]
   2d3b4:	90ffffe0 	adrp	x0, 29000 <NativeMG::Impl::coarse_solve_eo(std::vector<float, lqcd_native::WorkspaceAllocator<float> > const&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&) const+0x7c0>
   2d3b8:	52800141 	mov	w1, #0xa                   	// #10
   2d3bc:	9130c000 	add	x0, x0, #0xc30
   2d3c0:	f9401842 	ldr	x2, [x2, #48]
   2d3c4:	eb00005f 	cmp	x2, x0
   2d3c8:	54fffda0 	b.eq	2d37c <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1bc>  // b.none
   2d3cc:	aa1403e0 	mov	x0, x20
   2d3d0:	d63f0040 	blr	x2
   2d3d4:	12001c01 	and	w1, w0, #0xff
   2d3d8:	17ffffe9 	b	2d37c <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1bc>
   2d3dc:	b94a4373 	ldr	w19, [x27, #2624]
   2d3e0:	97ff60b0 	bl	56a0 <omp_get_max_threads@plt>
   2d3e4:	b90107e0 	str	w0, [sp, #260]
   2d3e8:	7100027f 	cmp	w19, #0x0
   2d3ec:	5400920c 	b.gt	2e62c <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x146c>
   2d3f0:	b9013bff 	str	wzr, [sp, #312]
   2d3f4:	b9413fe1 	ldr	w1, [sp, #316]
   2d3f8:	d2947ae2 	mov	x2, #0xa3d7                	// #41943
   2d3fc:	f2a7ae02 	movk	x2, #0x3d70, lsl #16
   2d400:	f2dae142 	movk	x2, #0xd70a, lsl #32
   2d404:	f2e01462 	movk	x2, #0xa3, lsl #48
   2d408:	93407c20 	sxtw	x0, w1
   2d40c:	eb02001f 	cmp	x0, x2
   2d410:	5400ce68 	b.hi	2eddc <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1c1c>  // b.pmore
   2d414:	52801902 	mov	w2, #0xc8                  	// #200
   2d418:	a9167fff 	stp	xzr, xzr, [sp, #352]
   2d41c:	f900bbff 	str	xzr, [sp, #368]
   2d420:	9b227c33 	smull	x19, w1, w2
   2d424:	b400bee0 	cbz	x0, 2ec00 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1a40>
   2d428:	aa1303e0 	mov	x0, x19
   2d42c:	97ff5f8d 	bl	5260 <operator new(unsigned long)@plt>
   2d430:	b9413ff4 	ldr	w20, [sp, #316]
   2d434:	8b130001 	add	x1, x0, x19
   2d438:	f900b3e0 	str	x0, [sp, #352]
   2d43c:	f900bbe1 	str	x1, [sp, #368]
   2d440:	93407e82 	sxtw	x2, w20
   2d444:	d503201f 	nop
   2d448:	a9007c1f 	stp	xzr, xzr, [x0]
   2d44c:	a9017c1f 	stp	xzr, xzr, [x0, #16]
   2d450:	a9027c1f 	stp	xzr, xzr, [x0, #32]
   2d454:	a9037c1f 	stp	xzr, xzr, [x0, #48]
   2d458:	a9047c1f 	stp	xzr, xzr, [x0, #64]
   2d45c:	a9057c1f 	stp	xzr, xzr, [x0, #80]
   2d460:	a9067c1f 	stp	xzr, xzr, [x0, #96]
   2d464:	a9077c1f 	stp	xzr, xzr, [x0, #112]
   2d468:	a9087c1f 	stp	xzr, xzr, [x0, #128]
   2d46c:	a9097c1f 	stp	xzr, xzr, [x0, #144]
   2d470:	91032000 	add	x0, x0, #0xc8
   2d474:	a93dfc1f 	stp	xzr, xzr, [x0, #-40]
   2d478:	a93efc1f 	stp	xzr, xzr, [x0, #-24]
   2d47c:	f81f801f 	stur	xzr, [x0, #-8]
   2d480:	eb00003f 	cmp	x1, x0
   2d484:	54fffe21 	b.ne	2d448 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x288>  // b.any
   2d488:	910583e6 	add	x6, sp, #0x160
   2d48c:	9104f3e4 	add	x4, sp, #0x13c
   2d490:	910533e3 	add	x3, sp, #0x14c
   2d494:	b9014fff 	str	wzr, [sp, #332]
   2d498:	910543e0 	add	x0, sp, #0x150
   2d49c:	92fe0005 	mov	x5, #0xfffffffffffffff     	// #1152921504606846975
   2d4a0:	f9008fe6 	str	x6, [sp, #280]
   2d4a4:	f900b7e1 	str	x1, [sp, #360]
   2d4a8:	f900d7e4 	str	x4, [sp, #424]
   2d4ac:	f900dbfb 	str	x27, [sp, #432]
   2d4b0:	f900dfe3 	str	x3, [sp, #440]
   2d4b4:	a91c03e6 	stp	x6, x0, [sp, #448]
   2d4b8:	eb05005f 	cmp	x2, x5
   2d4bc:	5400c968 	b.hi	2ede8 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1c28>  // b.pmore
   2d4c0:	d37df053 	lsl	x19, x2, #3
   2d4c4:	b400c662 	cbz	x2, 2ed90 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1bd0>
   2d4c8:	aa1303e0 	mov	x0, x19
   2d4cc:	97ff5f65 	bl	5260 <operator new(unsigned long)@plt>
   2d4d0:	8b130002 	add	x2, x0, x19
   2d4d4:	f90047e0 	str	x0, [sp, #136]
   2d4d8:	b9413ff4 	ldr	w20, [sp, #316]
   2d4dc:	f9006fe2 	str	x2, [sp, #216]
   2d4e0:	eb00005f 	cmp	x2, x0
   2d4e4:	54000080 	b.eq	2d4f4 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x334>  // b.none
   2d4e8:	aa1303e2 	mov	x2, x19
   2d4ec:	52800001 	mov	w1, #0x0                   	// #0
   2d4f0:	97ff5ef4 	bl	50c0 <memset@plt>
   2d4f4:	7100029f 	cmp	w20, #0x0
   2d4f8:	5400b9ed 	b.le	2ec34 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1a74>
   2d4fc:	910823e0 	add	x0, sp, #0x208
   2d500:	f94047e1 	ldr	x1, [sp, #136]
   2d504:	f0ffffb8 	adrp	x24, 24000 <(anonymous namespace)::coarse_gcr_fused_step(std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, double&) [clone ._omp_fn.1]+0x90>
   2d508:	d2835019 	mov	x25, #0x1a80                	// #6784
   2d50c:	f90057e0 	str	x0, [sp, #168]
   2d510:	f9406fe0 	ldr	x0, [sp, #216]
   2d514:	d2800016 	mov	x22, #0x0                   	// #0
   2d518:	d2800013 	mov	x19, #0x0                   	// #0
   2d51c:	0f000408 	movi	v8.2s, #0x0
   2d520:	912c4318 	add	x24, x24, #0xb10
   2d524:	d2800014 	mov	x20, #0x0                   	// #0
   2d528:	f2a000d9 	movk	x25, #0x6, lsl #16
   2d52c:	cb010017 	sub	x23, x0, x1
   2d530:	a94aebfc 	ldp	x28, x26, [sp, #168]
   2d534:	f9405fe0 	ldr	x0, [sp, #184]
   2d538:	f90063f7 	str	x23, [sp, #192]
   2d53c:	f9400341 	ldr	x1, [x26]
   2d540:	f9400000 	ldr	x0, [x0]
   2d544:	aa1c03e2 	mov	x2, x28
   2d548:	8b130024 	add	x4, x1, x19
   2d54c:	f8736823 	ldr	x3, [x1, x19]
   2d550:	8b130000 	add	x0, x0, x19
   2d554:	f9400481 	ldr	x1, [x4, #8]
   2d558:	bd020be8 	str	s8, [sp, #520]
   2d55c:	cb030021 	sub	x1, x1, x3
   2d560:	9342fc21 	asr	x1, x1, #2
   2d564:	97fff377 	bl	2a340 <std::vector<float, lqcd_native::WorkspaceAllocator<float> >::_M_fill_assign(unsigned long, float const&)>
   2d568:	f9400341 	ldr	x1, [x26]
   2d56c:	f940b3e0 	ldr	x0, [sp, #352]
   2d570:	aa1c03e2 	mov	x2, x28
   2d574:	f90063f7 	str	x23, [sp, #192]
   2d578:	8b130024 	add	x4, x1, x19
   2d57c:	f8736823 	ldr	x3, [x1, x19]
   2d580:	8b160000 	add	x0, x0, x22
   2d584:	f9400481 	ldr	x1, [x4, #8]
   2d588:	9100c000 	add	x0, x0, #0x30
   2d58c:	bd020be8 	str	s8, [sp, #520]
   2d590:	cb030021 	sub	x1, x1, x3
   2d594:	9342fc21 	asr	x1, x1, #2
   2d598:	97fff36a 	bl	2a340 <std::vector<float, lqcd_native::WorkspaceAllocator<float> >::_M_fill_assign(unsigned long, float const&)>
   2d59c:	f9400342 	ldr	x2, [x26]
   2d5a0:	aa1c03e1 	mov	x1, x28
   2d5a4:	aa1803e0 	mov	x0, x24
   2d5a8:	52800003 	mov	w3, #0x0                   	// #0
   2d5ac:	910322d6 	add	x22, x22, #0xc8
   2d5b0:	8b130044 	add	x4, x2, x19
   2d5b4:	f8736845 	ldr	x5, [x2, x19]
   2d5b8:	91006273 	add	x19, x19, #0x18
   2d5bc:	f9400482 	ldr	x2, [x4, #8]
   2d5c0:	f90107e4 	str	x4, [sp, #520]
   2d5c4:	f9010bff 	str	xzr, [sp, #528]
   2d5c8:	cb050042 	sub	x2, x2, x5
   2d5cc:	eb19005f 	cmp	x2, x25
   2d5d0:	1a9f87e2 	cset	w2, ls  // ls = plast
   2d5d4:	97ff5fe7 	bl	5570 <GOMP_parallel@plt>
   2d5d8:	fd410be0 	ldr	d0, [sp, #528]
   2d5dc:	f94047e1 	ldr	x1, [sp, #136]
   2d5e0:	b9413fe0 	ldr	w0, [sp, #316]
   2d5e4:	fc347820 	str	d0, [x1, x20, lsl #3]
   2d5e8:	91000694 	add	x20, x20, #0x1
   2d5ec:	6b14001f 	cmp	w0, w20
   2d5f0:	54fffa0c 	b.gt	2d530 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x370>
   2d5f4:	d0000281 	adrp	x1, 7f000 <__FRAME_END__+0x18c0c>
   2d5f8:	f9004be1 	str	x1, [sp, #144]
   2d5fc:	f9475821 	ldr	x1, [x1, #3760]
   2d600:	b9400021 	ldr	w1, [x1]
   2d604:	7100043f 	cmp	w1, #0x1
   2d608:	540082cc 	b.gt	2e660 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x14a0>
   2d60c:	b9414fe1 	ldr	w1, [sp, #332]
   2d610:	11000421 	add	w1, w1, #0x1
   2d614:	b9014fe1 	str	w1, [sp, #332]
   2d618:	7100001f 	cmp	w0, #0x0
   2d61c:	5400b1ed 	b.le	2ec58 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1a98>
   2d620:	f940b3e2 	ldr	x2, [sp, #352]
   2d624:	d2800014 	mov	x20, #0x0                   	// #0
   2d628:	d2800013 	mov	x19, #0x0                   	// #0
   2d62c:	d503201f 	nop
   2d630:	f94047e1 	ldr	x1, [sp, #136]
   2d634:	8b140056 	add	x22, x2, x20
   2d638:	fc737820 	ldr	d0, [x1, x19, lsl #3]
   2d63c:	1e602008 	fcmp	d0, #0.0
   2d640:	540001e5 	b.pl	2d67c <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x4bc>  // b.nfrst
   2d644:	97ff606f 	bl	5800 <sqrt@plt>
   2d648:	1e602008 	fcmp	d0, #0.0
   2d64c:	91000673 	add	x19, x19, #0x1
   2d650:	fd0056c0 	str	d0, [x22, #168]
   2d654:	b9413fe0 	ldr	w0, [sp, #316]
   2d658:	1a9f17e2 	cset	w2, eq  // eq = none
   2d65c:	1a9f07e1 	cset	w1, ne  // ne = any
   2d660:	91032294 	add	x20, x20, #0xc8
   2d664:	390312c2 	strb	w2, [x22, #196]
   2d668:	2a0102b5 	orr	w21, w21, w1
   2d66c:	6b13001f 	cmp	w0, w19
   2d670:	540001cd 	b.le	2d6a8 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x4e8>
   2d674:	f940b3e2 	ldr	x2, [sp, #352]
   2d678:	17ffffee 	b	2d630 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x470>
   2d67c:	1e61c000 	fsqrt	d0, d0
   2d680:	91000673 	add	x19, x19, #0x1
   2d684:	91032294 	add	x20, x20, #0xc8
   2d688:	1e602008 	fcmp	d0, #0.0
   2d68c:	fd0056c0 	str	d0, [x22, #168]
   2d690:	1a9f17e3 	cset	w3, eq  // eq = none
   2d694:	1a9f07e1 	cset	w1, ne  // ne = any
   2d698:	390312c3 	strb	w3, [x22, #196]
   2d69c:	2a0102b5 	orr	w21, w21, w1
   2d6a0:	6b13001f 	cmp	w0, w19
   2d6a4:	54fffc6c 	b.gt	2d630 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x470>
   2d6a8:	3400ad95 	cbz	w21, 2ec58 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1a98>
   2d6ac:	910823e1 	add	x1, sp, #0x208
   2d6b0:	9108a3e2 	add	x2, sp, #0x228
   2d6b4:	a9007c3f 	stp	xzr, xzr, [x1]
   2d6b8:	a9017c3f 	stp	xzr, xzr, [x1, #16]
   2d6bc:	a9007c5f 	stp	xzr, xzr, [x2]
   2d6c0:	a9017c5f 	stp	xzr, xzr, [x2, #16]
   2d6c4:	f90127ff 	str	xzr, [sp, #584]
   2d6c8:	7100001f 	cmp	w0, #0x0
   2d6cc:	5400050d 	b.le	2d76c <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x5ac>
   2d6d0:	910823e1 	add	x1, sp, #0x208
   2d6d4:	f94047e2 	ldr	x2, [sp, #136]
   2d6d8:	d2800015 	mov	x21, #0x0                   	// #0
   2d6dc:	d2800013 	mov	x19, #0x0                   	// #0
   2d6e0:	f90057e1 	str	x1, [sp, #168]
   2d6e4:	f9406fe1 	ldr	x1, [sp, #216]
   2d6e8:	9108e3f8 	add	x24, sp, #0x238
   2d6ec:	52800014 	mov	w20, #0x0                   	// #0
   2d6f0:	910743f6 	add	x22, sp, #0x1d0
   2d6f4:	cb020037 	sub	x23, x1, x2
   2d6f8:	14000006 	b	2d710 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x550>
   2d6fc:	11000694 	add	w20, w20, #0x1
   2d700:	91032273 	add	x19, x19, #0xc8
   2d704:	910062b5 	add	x21, x21, #0x18
   2d708:	6b00029f 	cmp	w20, w0
   2d70c:	5400034a 	b.ge	2d774 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x5b4>  // b.tcont
   2d710:	f940b3e2 	ldr	x2, [sp, #352]
   2d714:	8b130042 	add	x2, x2, x19
   2d718:	39431041 	ldrb	w1, [x2, #196]
   2d71c:	35ffff01 	cbnz	w1, 2d6fc <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x53c>
   2d720:	f9405be0 	ldr	x0, [sp, #176]
   2d724:	f9410be1 	ldr	x1, [sp, #528]
   2d728:	f9410fe3 	ldr	x3, [sp, #536]
   2d72c:	f9400000 	ldr	x0, [x0]
   2d730:	8b150000 	add	x0, x0, x21
   2d734:	f900ebe0 	str	x0, [sp, #464]
   2d738:	eb03003f 	cmp	x1, x3
   2d73c:	5400a180 	b.eq	2eb6c <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x19ac>  // b.none
   2d740:	f8008420 	str	x0, [x1], #8
   2d744:	f9010be1 	str	x1, [sp, #528]
   2d748:	f94123e1 	ldr	x1, [sp, #576]
   2d74c:	f94127e0 	ldr	x0, [sp, #584]
   2d750:	f900ebe2 	str	x2, [sp, #464]
   2d754:	eb00003f 	cmp	x1, x0
   2d758:	54009fe0 	b.eq	2eb54 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1994>  // b.none
   2d75c:	f8008422 	str	x2, [x1], #8
   2d760:	b9413fe0 	ldr	w0, [sp, #316]
   2d764:	f90123e1 	str	x1, [sp, #576]
   2d768:	17ffffe5 	b	2d6fc <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x53c>
   2d76c:	910823e0 	add	x0, sp, #0x208
   2d770:	f90057e0 	str	x0, [sp, #168]
   2d774:	f94047e4 	ldr	x4, [sp, #136]
   2d778:	f94057e0 	ldr	x0, [sp, #168]
   2d77c:	f9406fe3 	ldr	x3, [sp, #216]
   2d780:	9100c002 	add	x2, x0, #0x30
   2d784:	aa0003e1 	mov	x1, x0
   2d788:	aa1b03e0 	mov	x0, x27
   2d78c:	cb040063 	sub	x3, x3, x4
   2d790:	f90063e3 	str	x3, [sp, #192]
   2d794:	94001097 	bl	319f0 <NativeMG::Impl::coarse_reduced_rhs_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> > const*, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > const*> > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >*, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> >*> > const&) const>
   2d798:	b9413ff6 	ldr	w22, [sp, #316]
   2d79c:	710002df 	cmp	w22, #0x0
   2d7a0:	5400afed 	b.le	2ed9c <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1bdc>
   2d7a4:	f94047e1 	ldr	x1, [sp, #136]
   2d7a8:	f9406fe0 	ldr	x0, [sp, #216]
   2d7ac:	d2800014 	mov	x20, #0x0                   	// #0
   2d7b0:	52800013 	mov	w19, #0x0                   	// #0
   2d7b4:	cb010015 	sub	x21, x0, x1
   2d7b8:	14000005 	b	2d7cc <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x60c>
   2d7bc:	11000673 	add	w19, w19, #0x1
   2d7c0:	91032294 	add	x20, x20, #0xc8
   2d7c4:	6b16027f 	cmp	w19, w22
   2d7c8:	5400014a 	b.ge	2d7f0 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x630>  // b.tcont
   2d7cc:	f940b3e2 	ldr	x2, [sp, #352]
   2d7d0:	8b140041 	add	x1, x2, x20
   2d7d4:	39431020 	ldrb	w0, [x1, #196]
   2d7d8:	35ffff20 	cbnz	w0, 2d7bc <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x5fc>
   2d7dc:	91006020 	add	x0, x1, #0x18
   2d7e0:	f90063f5 	str	x21, [sp, #192]
   2d7e4:	97ffe433 	bl	268b0 <std::vector<float, lqcd_native::WorkspaceAllocator<float> >::operator=(std::vector<float, lqcd_native::WorkspaceAllocator<float> > const&) [clone .isra.0]>
   2d7e8:	b9413ff6 	ldr	w22, [sp, #316]
   2d7ec:	17fffff4 	b	2d7bc <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x5fc>
   2d7f0:	f94047e0 	ldr	x0, [sp, #136]
   2d7f4:	f9406fe1 	ldr	x1, [sp, #216]
   2d7f8:	eb01001f 	cmp	x0, x1
   2d7fc:	5400aec0 	b.eq	2edd4 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1c14>  // b.none
   2d800:	f94047e0 	ldr	x0, [sp, #136]
   2d804:	f9406fe1 	ldr	x1, [sp, #216]
   2d808:	cb000021 	sub	x1, x1, x0
   2d80c:	aa0103e2 	mov	x2, x1
   2d810:	52800001 	mov	w1, #0x0                   	// #0
   2d814:	f90063e2 	str	x2, [sp, #192]
   2d818:	97ff5e2a 	bl	50c0 <memset@plt>
   2d81c:	710002df 	cmp	w22, #0x0
   2d820:	5400ac8d 	b.le	2edb0 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1bf0>
   2d824:	f940b3e2 	ldr	x2, [sp, #352]
   2d828:	f0ffffb7 	adrp	x23, 24000 <(anonymous namespace)::coarse_gcr_fused_step(std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, double&) [clone ._omp_fn.1]+0x90>
   2d82c:	d2835013 	mov	x19, #0x1a80                	// #6784
   2d830:	d2800015 	mov	x21, #0x0                   	// #0
   2d834:	d2800014 	mov	x20, #0x0                   	// #0
   2d838:	2f00e408 	movi	d8, #0x0
   2d83c:	912c42f7 	add	x23, x23, #0xb10
   2d840:	f2a000d3 	movk	x19, #0x6, lsl #16
   2d844:	910743f8 	add	x24, sp, #0x1d0
   2d848:	8b150043 	add	x3, x2, x21
   2d84c:	39431064 	ldrb	w4, [x3, #196]
   2d850:	34006c24 	cbz	w4, 2e5d4 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1414>
   2d854:	91000694 	add	x20, x20, #0x1
   2d858:	910322b5 	add	x21, x21, #0xc8
   2d85c:	6b1402df 	cmp	w22, w20
   2d860:	54ffff4c 	b.gt	2d848 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x688>
   2d864:	f9404be0 	ldr	x0, [sp, #144]
   2d868:	f9475800 	ldr	x0, [x0, #3760]
   2d86c:	b9400000 	ldr	w0, [x0]
   2d870:	7100041f 	cmp	w0, #0x1
   2d874:	5400718c 	b.gt	2e6a4 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x14e4>
   2d878:	b9414fe0 	ldr	w0, [sp, #332]
   2d87c:	11000400 	add	w0, w0, #0x1
   2d880:	b9014fe0 	str	w0, [sp, #332]
   2d884:	710002df 	cmp	w22, #0x0
   2d888:	540002ad 	b.le	2d8dc <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x71c>
   2d88c:	d2800014 	mov	x20, #0x0                   	// #0
   2d890:	d2800013 	mov	x19, #0x0                   	// #0
   2d894:	d503201f 	nop
   2d898:	f94047e0 	ldr	x0, [sp, #136]
   2d89c:	fc737800 	ldr	d0, [x0, x19, lsl #3]
   2d8a0:	1e602008 	fcmp	d0, #0.0
   2d8a4:	540000c5 	b.pl	2d8bc <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x6fc>  // b.nfrst
   2d8a8:	97ff5fd6 	bl	5800 <sqrt@plt>
   2d8ac:	91000673 	add	x19, x19, #0x1
   2d8b0:	b9413ff6 	ldr	w22, [sp, #316]
   2d8b4:	f940b3e0 	ldr	x0, [sp, #352]
   2d8b8:	14000004 	b	2d8c8 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x708>
   2d8bc:	1e61c000 	fsqrt	d0, d0
   2d8c0:	f940b3e0 	ldr	x0, [sp, #352]
   2d8c4:	91000673 	add	x19, x19, #0x1
   2d8c8:	8b140000 	add	x0, x0, x20
   2d8cc:	91032294 	add	x20, x20, #0xc8
   2d8d0:	fd005800 	str	d0, [x0, #176]
   2d8d4:	6b1302df 	cmp	w22, w19
   2d8d8:	54fffe0c 	b.gt	2d898 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x6d8>
   2d8dc:	93407ec1 	sxtw	x1, w22
   2d8e0:	9105e3e0 	add	x0, sp, #0x178
   2d8e4:	a917ffff 	stp	xzr, xzr, [sp, #376]
   2d8e8:	a918ffff 	stp	xzr, xzr, [sp, #392]
   2d8ec:	f9007fe0 	str	x0, [sp, #248]
   2d8f0:	a919ffff 	stp	xzr, xzr, [sp, #408]
   2d8f4:	97ff5edf 	bl	5470 <std::vector<int, std::allocator<int> >::reserve(unsigned long)@plt>
   2d8f8:	b9813fe1 	ldrsw	x1, [sp, #316]
   2d8fc:	910643e0 	add	x0, sp, #0x190
   2d900:	f9008be0 	str	x0, [sp, #272]
   2d904:	97ff5edb 	bl	5470 <std::vector<int, std::allocator<int> >::reserve(unsigned long)@plt>
   2d908:	b9413ffc 	ldr	w28, [sp, #316]
   2d90c:	92fe0002 	mov	x2, #0xfffffffffffffff     	// #1152921504606846975
   2d910:	531f7b80 	lsl	w0, w28, #1
   2d914:	93407c01 	sxtw	x1, w0
   2d918:	eb02003f 	cmp	x1, x2
   2d91c:	5400a788 	b.hi	2ee0c <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1c4c>  // b.pmore
   2d920:	d37df033 	lsl	x19, x1, #3
   2d924:	b4006dc1 	cbz	x1, 2e6dc <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x151c>
   2d928:	aa1303e0 	mov	x0, x19
   2d92c:	97ff5e4d 	bl	5260 <operator new(unsigned long)@plt>
   2d930:	8b130001 	add	x1, x0, x19
   2d934:	b9413ffc 	ldr	w28, [sp, #316]
   2d938:	aa0003f8 	mov	x24, x0
   2d93c:	f9004fe1 	str	x1, [sp, #152]
   2d940:	eb00003f 	cmp	x1, x0
   2d944:	54000080 	b.eq	2d954 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x794>  // b.none
   2d948:	aa1303e2 	mov	x2, x19
   2d94c:	52800001 	mov	w1, #0x0                   	// #0
   2d950:	97ff5ddc 	bl	50c0 <memset@plt>
   2d954:	531f7b80 	lsl	w0, w28, #1
   2d958:	0b1c0000 	add	w0, w0, w28
   2d95c:	92fe0001 	mov	x1, #0xfffffffffffffff     	// #1152921504606846975
   2d960:	93407c00 	sxtw	x0, w0
   2d964:	eb01001f 	cmp	x0, x1
   2d968:	5400a468 	b.hi	2edf4 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1c34>  // b.pmore
   2d96c:	d37df013 	lsl	x19, x0, #3
   2d970:	b4009360 	cbz	x0, 2ebdc <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1a1c>
   2d974:	aa1303e0 	mov	x0, x19
   2d978:	97ff5e3a 	bl	5260 <operator new(unsigned long)@plt>
   2d97c:	8b130002 	add	x2, x0, x19
   2d980:	f90067e0 	str	x0, [sp, #200]
   2d984:	b9413ffc 	ldr	w28, [sp, #316]
   2d988:	f90073e2 	str	x2, [sp, #224]
   2d98c:	eb00005f 	cmp	x2, x0
   2d990:	54000080 	b.eq	2d9a0 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x7e0>  // b.none
   2d994:	aa1303e2 	mov	x2, x19
   2d998:	52800001 	mov	w1, #0x0                   	// #0
   2d99c:	97ff5dc9 	bl	50c0 <memset@plt>
   2d9a0:	b94b6360 	ldr	w0, [x27, #2912]
   2d9a4:	7100001f 	cmp	w0, #0x0
   2d9a8:	5400588d 	b.le	2e4b8 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x12f8>
   2d9ac:	f9404fe0 	ldr	x0, [sp, #152]
   2d9b0:	f94067e2 	ldr	x2, [sp, #200]
   2d9b4:	f94073e1 	ldr	x1, [sp, #224]
   2d9b8:	b90103ff 	str	wzr, [sp, #256]
   2d9bc:	cb180000 	sub	x0, x0, x24
   2d9c0:	cb020021 	sub	x1, x1, x2
   2d9c4:	f90053e0 	str	x0, [sp, #160]
   2d9c8:	d3438800 	ubfx	x0, x0, #3, #32
   2d9cc:	b0000182 	adrp	x2, 5e000 <typeinfo name for lqcd::Error+0x9b8>
   2d9d0:	f9006be0 	str	x0, [sp, #208]
   2d9d4:	d3438820 	ubfx	x0, x1, #3, #32
   2d9d8:	fd40084a 	ldr	d10, [x2, #16]
   2d9dc:	f90087e0 	str	x0, [sp, #264]
   2d9e0:	f94063e0 	ldr	x0, [sp, #192]
   2d9e4:	f90077e1 	str	x1, [sp, #232]
   2d9e8:	d3438800 	ubfx	x0, x0, #3, #32
   2d9ec:	f9007be0 	str	x0, [sp, #240]
   2d9f0:	a95783f5 	ldp	x21, x0, [sp, #376]
   2d9f4:	eb15001f 	cmp	x0, x21
   2d9f8:	54000040 	b.eq	2da00 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x840>  // b.none
   2d9fc:	f900c3f5 	str	x21, [sp, #384]
   2da00:	b9015bff 	str	wzr, [sp, #344]
   2da04:	7100039f 	cmp	w28, #0x0
   2da08:	5400558d 	b.le	2e4b8 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x12f8>
   2da0c:	f0ffffb7 	adrp	x23, 24000 <(anonymous namespace)::coarse_gcr_fused_step(std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, double&) [clone ._omp_fn.1]+0x90>
   2da10:	b201f3f9 	mov	x25, #0xaaaaaaaaaaaaaaaa    	// #-6148914691236517206
   2da14:	52800000 	mov	w0, #0x0                   	// #0
   2da18:	f90043ff 	str	xzr, [sp, #128]
   2da1c:	912f82f7 	add	x23, x23, #0xbe0
   2da20:	910743f6 	add	x22, sp, #0x1d0
   2da24:	f2955579 	movk	x25, #0xaaab
   2da28:	910563fa 	add	x26, sp, #0x158
   2da2c:	d503201f 	nop
   2da30:	f940b3e1 	ldr	x1, [sp, #352]
   2da34:	52801913 	mov	w19, #0xc8                  	// #200
   2da38:	9b330413 	smaddl	x19, w0, w19, x1
   2da3c:	39431261 	ldrb	w1, [x19, #196]
   2da40:	350000c1 	cbnz	w1, 2da58 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x898>
   2da44:	6d4a8662 	ldp	d2, d1, [x19, #168]
   2da48:	fd452b60 	ldr	d0, [x27, #2640]
   2da4c:	1e620800 	fmul	d0, d0, d2
   2da50:	1e602030 	fcmpe	d1, d0
   2da54:	540064aa 	b.ge	2e6e8 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1528>  // b.tcont
   2da58:	11000400 	add	w0, w0, #0x1
   2da5c:	b9015be0 	str	w0, [sp, #344]
   2da60:	6b1c001f 	cmp	w0, w28
   2da64:	54fffe6b 	b.lt	2da30 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x870>  // b.tstop
   2da68:	f940bff3 	ldr	x19, [sp, #376]
   2da6c:	f94107e1 	ldr	x1, [sp, #520]
   2da70:	f9410be0 	ldr	x0, [sp, #528]
   2da74:	aa0103e2 	mov	x2, x1
   2da78:	eb1302bf 	cmp	x21, x19
   2da7c:	54005220 	b.eq	2e4c0 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1300>  // b.none
   2da80:	eb00003f 	cmp	x1, x0
   2da84:	54000040 	b.eq	2da8c <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x8cc>  // b.none
   2da88:	f9010be1 	str	x1, [sp, #528]
   2da8c:	f9411fe0 	ldr	x0, [sp, #568]
   2da90:	f94123e2 	ldr	x2, [sp, #576]
   2da94:	eb02001f 	cmp	x0, x2
   2da98:	54000040 	b.eq	2daa0 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x8e0>  // b.none
   2da9c:	f90123e0 	str	x0, [sp, #576]
   2daa0:	f94057e0 	ldr	x0, [sp, #168]
   2daa4:	52801916 	mov	w22, #0xc8                  	// #200
   2daa8:	910743f7 	add	x23, sp, #0x1d0
   2daac:	9100c019 	add	x25, x0, #0x30
   2dab0:	1400000f 	b	2daec <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x92c>
   2dab4:	f8008422 	str	x2, [x1], #8
   2dab8:	f94127e2 	ldr	x2, [sp, #584]
   2dabc:	91018000 	add	x0, x0, #0x60
   2dac0:	f9010be1 	str	x1, [sp, #528]
   2dac4:	f94123e1 	ldr	x1, [sp, #576]
   2dac8:	f900ebe0 	str	x0, [sp, #464]
   2dacc:	eb02003f 	cmp	x1, x2
   2dad0:	54000380 	b.eq	2db40 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x980>  // b.none
   2dad4:	f8008420 	str	x0, [x1], #8
   2dad8:	91001273 	add	x19, x19, #0x4
   2dadc:	f90123e1 	str	x1, [sp, #576]
   2dae0:	eb1302bf 	cmp	x21, x19
   2dae4:	540003a0 	b.eq	2db58 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x998>  // b.none
   2dae8:	f9410be1 	ldr	x1, [sp, #528]
   2daec:	b9400274 	ldr	w20, [x19]
   2daf0:	f940b3e0 	ldr	x0, [sp, #352]
   2daf4:	f9410fe3 	ldr	x3, [sp, #536]
   2daf8:	9b367e94 	smull	x20, w20, w22
   2dafc:	8b140000 	add	x0, x0, x20
   2db00:	91012002 	add	x2, x0, #0x48
   2db04:	f900ebe2 	str	x2, [sp, #464]
   2db08:	eb01007f 	cmp	x3, x1
   2db0c:	54fffd41 	b.ne	2dab4 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x8f4>  // b.any
   2db10:	f94057e0 	ldr	x0, [sp, #168]
   2db14:	aa1703e2 	mov	x2, x23
   2db18:	97fffd12 	bl	2cf60 <void std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> > const*, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > const*> >::_M_realloc_insert<std::vector<float, lqcd_native::WorkspaceAllocator<float> > const*>(__gnu_cxx::__normal_iterator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > const**, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> > const*, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > const*> > >, std::vector<float, lqcd_native::WorkspaceAllocator<float> > const*&&)>
   2db1c:	f940b3e0 	ldr	x0, [sp, #352]
   2db20:	f94123e1 	ldr	x1, [sp, #576]
   2db24:	f94127e2 	ldr	x2, [sp, #584]
   2db28:	8b140000 	add	x0, x0, x20
   2db2c:	91018000 	add	x0, x0, #0x60
   2db30:	f900ebe0 	str	x0, [sp, #464]
   2db34:	eb02003f 	cmp	x1, x2
   2db38:	54fffce1 	b.ne	2dad4 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x914>  // b.any
   2db3c:	d503201f 	nop
   2db40:	aa1703e2 	mov	x2, x23
   2db44:	aa1903e0 	mov	x0, x25
   2db48:	97fffd52 	bl	2d090 <void std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >*, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> >*> >::_M_realloc_insert<std::vector<float, lqcd_native::WorkspaceAllocator<float> >*>(__gnu_cxx::__normal_iterator<std::vector<float, lqcd_native::WorkspaceAllocator<float> >**, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >*, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> >*> > >, std::vector<float, lqcd_native::WorkspaceAllocator<float> >*&&)>
   2db4c:	91001273 	add	x19, x19, #0x4
   2db50:	eb1302bf 	cmp	x21, x19
   2db54:	54fffca1 	b.ne	2dae8 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x928>  // b.any
   2db58:	f94057e0 	ldr	x0, [sp, #168]
   2db5c:	9100c002 	add	x2, x0, #0x30
   2db60:	aa0003e1 	mov	x1, x0
   2db64:	aa1b03e0 	mov	x0, x27
   2db68:	94000dfe 	bl	31360 <NativeMG::Impl::coarse_schur_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> > const*, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > const*> > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >*, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> >*> > const&) const>
   2db6c:	f94043e0 	ldr	x0, [sp, #128]
   2db70:	a957d3f9 	ldp	x25, x20, [sp, #376]
   2db74:	b4000c80 	cbz	x0, 2dd04 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xb44>
   2db78:	b201f3f7 	mov	x23, #0xaaaaaaaaaaaaaaaa    	// #-6148914691236517206
   2db7c:	d2800016 	mov	x22, #0x0                   	// #0
   2db80:	d2800015 	mov	x21, #0x0                   	// #0
   2db84:	f2955577 	movk	x23, #0xaaab
   2db88:	910743fc 	add	x28, sp, #0x1d0
   2db8c:	d503201f 	nop
   2db90:	f9404fe0 	ldr	x0, [sp, #152]
   2db94:	eb00031f 	cmp	x24, x0
   2db98:	540000a0 	b.eq	2dbac <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x9ec>  // b.none
   2db9c:	f94053e2 	ldr	x2, [sp, #160]
   2dba0:	52800001 	mov	w1, #0x0                   	// #0
   2dba4:	aa1803e0 	mov	x0, x24
   2dba8:	97ff5d46 	bl	50c0 <memset@plt>
   2dbac:	f0ffffb3 	adrp	x19, 24000 <(anonymous namespace)::coarse_gcr_fused_step(std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, double&) [clone ._omp_fn.1]+0x90>
   2dbb0:	911bc273 	add	x19, x19, #0x6f0
   2dbb4:	eb19029f 	cmp	x20, x25
   2dbb8:	54000460 	b.eq	2dc44 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xa84>  // b.none
   2dbbc:	d503201f 	nop
   2dbc0:	b940033a 	ldr	w26, [x25]
   2dbc4:	f940b3e0 	ldr	x0, [sp, #352]
   2dbc8:	52801903 	mov	w3, #0xc8                  	// #200
   2dbcc:	9b230343 	smaddl	x3, w26, w3, x0
   2dbd0:	a9490860 	ldp	x0, x2, [x3, #144]
   2dbd4:	cb000042 	sub	x2, x2, x0
   2dbd8:	9343fc42 	asr	x2, x2, #3
   2dbdc:	9b177c42 	mul	x2, x2, x23
   2dbe0:	eb15005f 	cmp	x2, x21
   2dbe4:	540002a9 	b.ls	2dc38 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xa78>  // b.plast
   2dbe8:	8b160005 	add	x5, x0, x22
   2dbec:	f8766806 	ldr	x6, [x0, x22]
   2dbf0:	91018062 	add	x2, x3, #0x60
   2dbf4:	aa1c03e1 	mov	x1, x28
   2dbf8:	f94004a4 	ldr	x4, [x5, #8]
   2dbfc:	a91d0be5 	stp	x5, x2, [sp, #464]
   2dc00:	52800003 	mov	w3, #0x0                   	// #0
   2dc04:	aa1303e0 	mov	x0, x19
   2dc08:	a91e7fff 	stp	xzr, xzr, [sp, #480]
   2dc0c:	531f7b5a 	lsl	w26, w26, #1
   2dc10:	937d7f5a 	sbfiz	x26, x26, #3, #32
   2dc14:	cb060082 	sub	x2, x4, x6
   2dc18:	d2835004 	mov	x4, #0x1a80                	// #6784
   2dc1c:	f2a000c4 	movk	x4, #0x6, lsl #16
   2dc20:	eb04005f 	cmp	x2, x4
   2dc24:	1a9f87e2 	cset	w2, ls  // ls = plast
   2dc28:	97ff5e52 	bl	5570 <GOMP_parallel@plt>
   2dc2c:	3dc07be0 	ldr	q0, [sp, #480]
   2dc30:	6e004000 	ext	v0.16b, v0.16b, v0.16b, #8
   2dc34:	3cba6b00 	str	q0, [x24, x26]
   2dc38:	91001339 	add	x25, x25, #0x4
   2dc3c:	eb19029f 	cmp	x20, x25
   2dc40:	54fffc01 	b.ne	2dbc0 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xa00>  // b.any
   2dc44:	f9404be0 	ldr	x0, [sp, #144]
   2dc48:	f9475800 	ldr	x0, [x0, #3760]
   2dc4c:	b9400000 	ldr	w0, [x0]
   2dc50:	7100041f 	cmp	w0, #0x1
   2dc54:	54005dcc 	b.gt	2e80c <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x164c>
   2dc58:	b9414fe0 	ldr	w0, [sp, #332]
   2dc5c:	a957e7f4 	ldp	x20, x25, [sp, #376]
   2dc60:	11000400 	add	w0, w0, #0x1
   2dc64:	b9014fe0 	str	w0, [sp, #332]
   2dc68:	eb14033f 	cmp	x25, x20
   2dc6c:	54005f20 	b.eq	2e850 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1690>  // b.none
   2dc70:	5280191a 	mov	w26, #0xc8                  	// #200
   2dc74:	d503201f 	nop
   2dc78:	b9400282 	ldr	w2, [x20]
   2dc7c:	f940b3f3 	ldr	x19, [sp, #352]
   2dc80:	9b3a4c53 	smaddl	x19, w2, w26, x19
   2dc84:	a9490261 	ldp	x1, x0, [x19, #144]
   2dc88:	cb010000 	sub	x0, x0, x1
   2dc8c:	9343fc00 	asr	x0, x0, #3
   2dc90:	9b177c00 	mul	x0, x0, x23
   2dc94:	eb15001f 	cmp	x0, x21
   2dc98:	54000249 	b.ls	2dce0 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xb20>  // b.plast
   2dc9c:	531f7842 	lsl	w2, w2, #1
   2dca0:	11000440 	add	w0, w2, #0x1
   2dca4:	fc62db09 	ldr	d9, [x24, w2, sxtw #3]
   2dca8:	8b160021 	add	x1, x1, x22
   2dcac:	fc60db08 	ldr	d8, [x24, w0, sxtw #3]
   2dcb0:	91018260 	add	x0, x19, #0x60
   2dcb4:	1e614129 	fneg	d9, d9
   2dcb8:	1e614108 	fneg	d8, d8
   2dcbc:	1e604120 	fmov	d0, d9
   2dcc0:	1e604101 	fmov	d1, d8
   2dcc4:	97ff7eaf 	bl	d780 <lqcd_native::detail::coarse_axpy(std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::complex<double>, std::vector<float, lqcd_native::WorkspaceAllocator<float> > const&)>
   2dcc8:	f9403e61 	ldr	x1, [x19, #120]
   2dccc:	1e604120 	fmov	d0, d9
   2dcd0:	91012260 	add	x0, x19, #0x48
   2dcd4:	1e604101 	fmov	d1, d8
   2dcd8:	8b160021 	add	x1, x1, x22
   2dcdc:	97ff7ea9 	bl	d780 <lqcd_native::detail::coarse_axpy(std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::complex<double>, std::vector<float, lqcd_native::WorkspaceAllocator<float> > const&)>
   2dce0:	91001294 	add	x20, x20, #0x4
   2dce4:	eb14033f 	cmp	x25, x20
   2dce8:	54fffc81 	b.ne	2dc78 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xab8>  // b.any
   2dcec:	a957d3f9 	ldp	x25, x20, [sp, #376]
   2dcf0:	f94043e0 	ldr	x0, [sp, #128]
   2dcf4:	910006b5 	add	x21, x21, #0x1
   2dcf8:	910062d6 	add	x22, x22, #0x18
   2dcfc:	eb0002bf 	cmp	x21, x0
   2dd00:	54fff481 	b.ne	2db90 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x9d0>  // b.any
   2dd04:	f94067e0 	ldr	x0, [sp, #200]
   2dd08:	f94073e1 	ldr	x1, [sp, #224]
   2dd0c:	eb01001f 	cmp	x0, x1
   2dd10:	54000080 	b.eq	2dd20 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xb60>  // b.none
   2dd14:	f94077e2 	ldr	x2, [sp, #232]
   2dd18:	52800001 	mov	w1, #0x0                   	// #0
   2dd1c:	97ff5ce9 	bl	50c0 <memset@plt>
   2dd20:	eb19029f 	cmp	x20, x25
   2dd24:	54000480 	b.eq	2ddb4 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xbf4>  // b.none
   2dd28:	f94067fa 	ldr	x26, [sp, #200]
   2dd2c:	f0ffffb6 	adrp	x22, 24000 <(anonymous namespace)::coarse_gcr_fused_step(std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, double&) [clone ._omp_fn.1]+0x90>
   2dd30:	910743f7 	add	x23, sp, #0x1d0
   2dd34:	2f00e408 	movi	d8, #0x0
   2dd38:	912002d6 	add	x22, x22, #0x800
   2dd3c:	52801913 	mov	w19, #0xc8                  	// #200
   2dd40:	b8404735 	ldr	w21, [x25], #4
   2dd44:	f940b3e2 	ldr	x2, [sp, #352]
   2dd48:	aa1703e1 	mov	x1, x23
   2dd4c:	aa1603e0 	mov	x0, x22
   2dd50:	52800003 	mov	w3, #0x0                   	// #0
   2dd54:	9b330aa2 	smaddl	x2, w21, w19, x2
   2dd58:	0b1506b5 	add	w21, w21, w21, lsl #1
   2dd5c:	f9403046 	ldr	x6, [x2, #96]
   2dd60:	f9403444 	ldr	x4, [x2, #104]
   2dd64:	91018045 	add	x5, x2, #0x60
   2dd68:	91006042 	add	x2, x2, #0x18
   2dd6c:	a91d0be5 	stp	x5, x2, [sp, #464]
   2dd70:	6d1e23e8 	stp	d8, d8, [sp, #480]
   2dd74:	fd00fbe8 	str	d8, [sp, #496]
   2dd78:	8b35cf55 	add	x21, x26, w21, sxtw #3
   2dd7c:	cb060082 	sub	x2, x4, x6
   2dd80:	d2835004 	mov	x4, #0x1a80                	// #6784
   2dd84:	f2a000c4 	movk	x4, #0x6, lsl #16
   2dd88:	eb04005f 	cmp	x2, x4
   2dd8c:	1a9f87e2 	cset	w2, ls  // ls = plast
   2dd90:	97ff5df8 	bl	5570 <GOMP_parallel@plt>
   2dd94:	6d5e87e0 	ldp	d0, d1, [sp, #488]
   2dd98:	6d1d03e1 	stp	d1, d0, [sp, #464]
   2dd9c:	a94006e0 	ldp	x0, x1, [x23]
   2dda0:	f9400ae2 	ldr	x2, [x23, #16]
   2dda4:	a90006a0 	stp	x0, x1, [x21]
   2dda8:	f9000aa2 	str	x2, [x21, #16]
   2ddac:	eb19029f 	cmp	x20, x25
   2ddb0:	54fffc81 	b.ne	2dd40 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xb80>  // b.any
   2ddb4:	f9404be0 	ldr	x0, [sp, #144]
   2ddb8:	f9475800 	ldr	x0, [x0, #3760]
   2ddbc:	b9400000 	ldr	w0, [x0]
   2ddc0:	7100041f 	cmp	w0, #0x1
   2ddc4:	5400554c 	b.gt	2e86c <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x16ac>
   2ddc8:	b9414fe0 	ldr	w0, [sp, #332]
   2ddcc:	f9406fe1 	ldr	x1, [sp, #216]
   2ddd0:	11000400 	add	w0, w0, #0x1
   2ddd4:	b9014fe0 	str	w0, [sp, #332]
   2ddd8:	f94047e0 	ldr	x0, [sp, #136]
   2dddc:	eb01001f 	cmp	x0, x1
   2dde0:	54000080 	b.eq	2ddf0 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xc30>  // b.none
   2dde4:	f94063e2 	ldr	x2, [sp, #192]
   2dde8:	52800001 	mov	w1, #0x0                   	// #0
   2ddec:	97ff5cb5 	bl	50c0 <memset@plt>
   2ddf0:	a957f3f9 	ldp	x25, x28, [sp, #376]
   2ddf4:	eb19039f 	cmp	x28, x25
   2ddf8:	54000760 	b.eq	2dee4 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xd24>  // b.none
   2ddfc:	f90043f8 	str	x24, [sp, #128]
   2de00:	aa1c03f8 	mov	x24, x28
   2de04:	f94047fa 	ldr	x26, [sp, #136]
   2de08:	f0ffffb3 	adrp	x19, 24000 <(anonymous namespace)::coarse_gcr_fused_step(std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, double&) [clone ._omp_fn.1]+0x90>
   2de0c:	f94067fc 	ldr	x28, [sp, #200]
   2de10:	910743f4 	add	x20, sp, #0x1d0
   2de14:	91250273 	add	x19, x19, #0x940
   2de18:	b9400337 	ldr	w23, [x25]
   2de1c:	f940b3e0 	ldr	x0, [sp, #352]
   2de20:	52801915 	mov	w21, #0xc8                  	// #200
   2de24:	0b1706e2 	add	w2, w23, w23, lsl #1
   2de28:	9b3502f5 	smaddl	x21, w23, w21, x0
   2de2c:	fc62db80 	ldr	d0, [x28, w2, sxtw #3]
   2de30:	8b22cf96 	add	x22, x28, w2, sxtw #3
   2de34:	1e602008 	fcmp	d0, #0.0
   2de38:	54004b45 	b.pl	2e7a0 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x15e0>  // b.nfrst
   2de3c:	97ff5e71 	bl	5800 <sqrt@plt>
   2de40:	1e6a2010 	fcmpe	d0, d10
   2de44:	54004de4 	b.mi	2e800 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1640>  // b.first
   2de48:	fd4002c0 	ldr	d0, [x22]
   2de4c:	910182a0 	add	x0, x21, #0x60
   2de50:	910122a5 	add	x5, x21, #0x48
   2de54:	9100c2a4 	add	x4, x21, #0x30
   2de58:	910062b5 	add	x21, x21, #0x18
   2de5c:	1e602008 	fcmp	d0, #0.0
   2de60:	54007d25 	b.pl	2ee04 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1c44>  // b.nfrst
   2de64:	a91213e5 	stp	x5, x4, [sp, #288]
   2de68:	f9009be0 	str	x0, [sp, #304]
   2de6c:	97ff5e65 	bl	5800 <sqrt@plt>
   2de70:	a95213e5 	ldp	x5, x4, [sp, #288]
   2de74:	f9409be0 	ldr	x0, [sp, #304]
   2de78:	6d4086c2 	ldp	d2, d1, [x22, #8]
   2de7c:	a9400807 	ldp	x7, x2, [x0]
   2de80:	52800003 	mov	w3, #0x0                   	// #0
   2de84:	aa1403e1 	mov	x1, x20
   2de88:	fd00fbe0 	str	d0, [sp, #496]
   2de8c:	a91e57e4 	stp	x4, x21, [sp, #480]
   2de90:	d2835004 	mov	x4, #0x1a80                	// #6784
   2de94:	f2a000c4 	movk	x4, #0x6, lsl #16
   2de98:	a91d17e0 	stp	x0, x5, [sp, #464]
   2de9c:	aa1303e0 	mov	x0, x19
   2dea0:	f900ffff 	str	xzr, [sp, #504]
   2dea4:	cb070042 	sub	x2, x2, x7
   2dea8:	eb04005f 	cmp	x2, x4
   2deac:	1e601842 	fdiv	d2, d2, d0
   2deb0:	1a9f87e2 	cset	w2, ls  // ls = plast
   2deb4:	1e601820 	fdiv	d0, d1, d0
   2deb8:	1e624041 	fcvt	s1, d2
   2debc:	1e624000 	fcvt	s0, d0
   2dec0:	bd0203e1 	str	s1, [sp, #512]
   2dec4:	bd0207e0 	str	s0, [sp, #516]
   2dec8:	97ff5daa 	bl	5570 <GOMP_parallel@plt>
   2decc:	fd40ffe0 	ldr	d0, [sp, #504]
   2ded0:	fc37db40 	str	d0, [x26, w23, sxtw #3]
   2ded4:	91001339 	add	x25, x25, #0x4
   2ded8:	eb18033f 	cmp	x25, x24
   2dedc:	54fff9e1 	b.ne	2de18 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xc58>  // b.any
   2dee0:	f94043f8 	ldr	x24, [sp, #128]
   2dee4:	f9404be0 	ldr	x0, [sp, #144]
   2dee8:	f9475800 	ldr	x0, [x0, #3760]
   2deec:	b9400000 	ldr	w0, [x0]
   2def0:	7100041f 	cmp	w0, #0x1
   2def4:	54004d4c 	b.gt	2e89c <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x16dc>
   2def8:	b9414fe0 	ldr	w0, [sp, #332]
   2defc:	a9590be1 	ldp	x1, x2, [sp, #400]
   2df00:	11000400 	add	w0, w0, #0x1
   2df04:	b9014fe0 	str	w0, [sp, #332]
   2df08:	eb02003f 	cmp	x1, x2
   2df0c:	54000040 	b.eq	2df14 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xd54>  // b.none
   2df10:	f900cfe1 	str	x1, [sp, #408]
   2df14:	a957d7f4 	ldp	x20, x21, [sp, #376]
   2df18:	eb1402bf 	cmp	x21, x20
   2df1c:	54002c00 	b.eq	2e49c <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x12dc>  // b.none
   2df20:	52801916 	mov	w22, #0xc8                  	// #200
   2df24:	910743f7 	add	x23, sp, #0x1d0
   2df28:	14000004 	b	2df38 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xd78>
   2df2c:	91001294 	add	x20, x20, #0x4
   2df30:	eb1402bf 	cmp	x21, x20
   2df34:	540007c0 	b.eq	2e02c <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xe6c>  // b.none
   2df38:	b9400280 	ldr	w0, [x20]
   2df3c:	f940b3f3 	ldr	x19, [sp, #352]
   2df40:	9b364c13 	smaddl	x19, w0, w22, x19
   2df44:	39431261 	ldrb	w1, [x19, #196]
   2df48:	b901d3e0 	str	w0, [sp, #464]
   2df4c:	35ffff01 	cbnz	w1, 2df2c <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xd6c>
   2df50:	f94047e1 	ldr	x1, [sp, #136]
   2df54:	fc60d820 	ldr	d0, [x1, w0, sxtw #3]
   2df58:	1e602008 	fcmp	d0, #0.0
   2df5c:	54004325 	b.pl	2e7c0 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1600>  // b.nfrst
   2df60:	97ff5e28 	bl	5800 <sqrt@plt>
   2df64:	9101e260 	add	x0, x19, #0x78
   2df68:	a9408801 	ldp	x1, x2, [x0, #8]
   2df6c:	fd005a60 	str	d0, [x19, #176]
   2df70:	eb02003f 	cmp	x1, x2
   2df74:	54004320 	b.eq	2e7d8 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1618>  // b.none
   2df78:	aa1303e2 	mov	x2, x19
   2df7c:	91006023 	add	x3, x1, #0x18
   2df80:	3cc48c40 	ldr	q0, [x2, #72]!
   2df84:	f9400844 	ldr	x4, [x2, #16]
   2df88:	f900085f 	str	xzr, [x2, #16]
   2df8c:	3d800020 	str	q0, [x1]
   2df90:	a904fe7f 	stp	xzr, xzr, [x19, #72]
   2df94:	f9000824 	str	x4, [x1, #16]
   2df98:	f9000403 	str	x3, [x0, #8]
   2df9c:	91024260 	add	x0, x19, #0x90
   2dfa0:	a9408801 	ldp	x1, x2, [x0, #8]
   2dfa4:	eb02003f 	cmp	x1, x2
   2dfa8:	54004240 	b.eq	2e7f0 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1630>  // b.none
   2dfac:	aa1303e3 	mov	x3, x19
   2dfb0:	91006022 	add	x2, x1, #0x18
   2dfb4:	3cc60c60 	ldr	q0, [x3, #96]!
   2dfb8:	f9400864 	ldr	x4, [x3, #16]
   2dfbc:	f900087f 	str	xzr, [x3, #16]
   2dfc0:	3d800020 	str	q0, [x1]
   2dfc4:	a9067e7f 	stp	xzr, xzr, [x19, #96]
   2dfc8:	f9000824 	str	x4, [x1, #16]
   2dfcc:	f9000402 	str	x2, [x0, #8]
   2dfd0:	6d4a8662 	ldp	d2, d1, [x19, #168]
   2dfd4:	fd452b60 	ldr	d0, [x27, #2640]
   2dfd8:	f9404a60 	ldr	x0, [x19, #144]
   2dfdc:	cb000042 	sub	x2, x2, x0
   2dfe0:	1e620800 	fmul	d0, d0, d2
   2dfe4:	1e602030 	fcmpe	d1, d0
   2dfe8:	54000064 	b.mi	2dff4 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xe34>  // b.first
   2dfec:	f106005f 	cmp	x2, #0x180
   2dff0:	54fff9e1 	b.ne	2df2c <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xd6c>  // b.any
   2dff4:	29578263 	ldp	w3, w0, [x19, #188]
   2dff8:	a95993e1 	ldp	x1, x4, [sp, #408]
   2dffc:	f106005f 	cmp	x2, #0x180
   2e000:	1a831462 	cinc	w2, w3, eq  // eq = none
   2e004:	11000400 	add	w0, w0, #0x1
   2e008:	29178262 	stp	w2, w0, [x19, #188]
   2e00c:	eb04003f 	cmp	x1, x4
   2e010:	540045e0 	b.eq	2e8cc <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x170c>  // b.none
   2e014:	b941d3e0 	ldr	w0, [sp, #464]
   2e018:	91001294 	add	x20, x20, #0x4
   2e01c:	b8004420 	str	w0, [x1], #4
   2e020:	f900cfe1 	str	x1, [sp, #408]
   2e024:	eb1402bf 	cmp	x21, x20
   2e028:	54fff881 	b.ne	2df38 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xd78>  // b.any
   2e02c:	a95913e2 	ldp	x2, x4, [sp, #400]
   2e030:	eb04005f 	cmp	x2, x4
   2e034:	54002340 	b.eq	2e49c <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x12dc>  // b.none
   2e038:	b200f3e1 	mov	x1, #0x5555555555555555    	// #6148914691236517205
   2e03c:	cb020080 	sub	x0, x4, x2
   2e040:	f2e2aaa1 	movk	x1, #0x1555, lsl #48
   2e044:	9342fc13 	asr	x19, x0, #2
   2e048:	eb01001f 	cmp	x0, x1
   2e04c:	54006e62 	b.cs	2ee18 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1c58>  // b.hs, b.nlast
   2e050:	8b130674 	add	x20, x19, x19, lsl #1
   2e054:	a91d7fff 	stp	xzr, xzr, [sp, #464]
   2e058:	f900f3ff 	str	xzr, [sp, #480]
   2e05c:	d37df294 	lsl	x20, x20, #3
   2e060:	b4005c93 	cbz	x19, 2ebf0 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1a30>
   2e064:	aa1403e0 	mov	x0, x20
   2e068:	97ff5c7e 	bl	5260 <operator new(unsigned long)@plt>
   2e06c:	8b140014 	add	x20, x0, x20
   2e070:	d1000663 	sub	x3, x19, #0x1
   2e074:	f900ebe0 	str	x0, [sp, #464]
   2e078:	aa0003e1 	mov	x1, x0
   2e07c:	f900f3f4 	str	x20, [sp, #480]
   2e080:	a95913e2 	ldp	x2, x4, [sp, #400]
   2e084:	f100287f 	cmp	x3, #0xa
   2e088:	54005b09 	b.ls	2ebe8 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1a28>  // b.plast
   2e08c:	927ffa63 	and	x3, x19, #0xfffffffffffffffe
   2e090:	4f000400 	movi	v0.4s, #0x0
   2e094:	8b530463 	add	x3, x3, x19, lsr #1
   2e098:	8b031003 	add	x3, x0, x3, lsl #4
   2e09c:	d503201f 	nop
   2e0a0:	ad000000 	stp	q0, q0, [x0]
   2e0a4:	9100c000 	add	x0, x0, #0x30
   2e0a8:	3c9f0000 	stur	q0, [x0, #-16]
   2e0ac:	eb00007f 	cmp	x3, x0
   2e0b0:	54ffff81 	b.ne	2e0a0 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xee0>  // b.any
   2e0b4:	927ffa60 	and	x0, x19, #0xfffffffffffffffe
   2e0b8:	92400265 	and	x5, x19, #0x1
   2e0bc:	8b000403 	add	x3, x0, x0, lsl #1
   2e0c0:	8b030c21 	add	x1, x1, x3, lsl #3
   2e0c4:	eb13001f 	cmp	x0, x19
   2e0c8:	54000560 	b.eq	2e174 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xfb4>  // b.none
   2e0cc:	a9007c3f 	stp	xzr, xzr, [x1]
   2e0d0:	f900083f 	str	xzr, [x1, #16]
   2e0d4:	f10004bf 	cmp	x5, #0x1
   2e0d8:	540004e0 	b.eq	2e174 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xfb4>  // b.none
   2e0dc:	a901fc3f 	stp	xzr, xzr, [x1, #24]
   2e0e0:	f900143f 	str	xzr, [x1, #40]
   2e0e4:	f10008bf 	cmp	x5, #0x2
   2e0e8:	54000460 	b.eq	2e174 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xfb4>  // b.none
   2e0ec:	a9037c3f 	stp	xzr, xzr, [x1, #48]
   2e0f0:	f900203f 	str	xzr, [x1, #64]
   2e0f4:	f1000cbf 	cmp	x5, #0x3
   2e0f8:	540003e0 	b.eq	2e174 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xfb4>  // b.none
   2e0fc:	a904fc3f 	stp	xzr, xzr, [x1, #72]
   2e100:	f9002c3f 	str	xzr, [x1, #88]
   2e104:	f10010bf 	cmp	x5, #0x4
   2e108:	54000360 	b.eq	2e174 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xfb4>  // b.none
   2e10c:	a9067c3f 	stp	xzr, xzr, [x1, #96]
   2e110:	f900383f 	str	xzr, [x1, #112]
   2e114:	f10014bf 	cmp	x5, #0x5
   2e118:	540002e0 	b.eq	2e174 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xfb4>  // b.none
   2e11c:	a907fc3f 	stp	xzr, xzr, [x1, #120]
   2e120:	f900443f 	str	xzr, [x1, #136]
   2e124:	f10018bf 	cmp	x5, #0x6
   2e128:	54000260 	b.eq	2e174 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xfb4>  // b.none
   2e12c:	a9097c3f 	stp	xzr, xzr, [x1, #144]
   2e130:	f900503f 	str	xzr, [x1, #160]
   2e134:	f1001cbf 	cmp	x5, #0x7
   2e138:	540001e0 	b.eq	2e174 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xfb4>  // b.none
   2e13c:	a90afc3f 	stp	xzr, xzr, [x1, #168]
   2e140:	f9005c3f 	str	xzr, [x1, #184]
   2e144:	f10020bf 	cmp	x5, #0x8
   2e148:	54000160 	b.eq	2e174 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xfb4>  // b.none
   2e14c:	a90c7c3f 	stp	xzr, xzr, [x1, #192]
   2e150:	f900683f 	str	xzr, [x1, #208]
   2e154:	f10024bf 	cmp	x5, #0x9
   2e158:	540000e0 	b.eq	2e174 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xfb4>  // b.none
   2e15c:	a90dfc3f 	stp	xzr, xzr, [x1, #216]
   2e160:	f900743f 	str	xzr, [x1, #232]
   2e164:	f10028bf 	cmp	x5, #0xa
   2e168:	54000060 	b.eq	2e174 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xfb4>  // b.none
   2e16c:	a90f7c3f 	stp	xzr, xzr, [x1, #240]
   2e170:	f900803f 	str	xzr, [x1, #256]
   2e174:	f94107e1 	ldr	x1, [sp, #520]
   2e178:	f9410be0 	ldr	x0, [sp, #528]
   2e17c:	f900eff4 	str	x20, [sp, #472]
   2e180:	eb00003f 	cmp	x1, x0
   2e184:	54000040 	b.eq	2e18c <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xfcc>  // b.none
   2e188:	f9010be1 	str	x1, [sp, #528]
   2e18c:	f9411fe0 	ldr	x0, [sp, #568]
   2e190:	f94123e3 	ldr	x3, [sp, #576]
   2e194:	eb03001f 	cmp	x0, x3
   2e198:	54000040 	b.eq	2e1a0 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xfe0>  // b.none
   2e19c:	f90123e0 	str	x0, [sp, #576]
   2e1a0:	eb02009f 	cmp	x4, x2
   2e1a4:	540006a0 	b.eq	2e278 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x10b8>  // b.none
   2e1a8:	f94057e0 	ldr	x0, [sp, #168]
   2e1ac:	d2800014 	mov	x20, #0x0                   	// #0
   2e1b0:	d2800013 	mov	x19, #0x0                   	// #0
   2e1b4:	52801915 	mov	w21, #0xc8                  	// #200
   2e1b8:	910563f6 	add	x22, sp, #0x158
   2e1bc:	9100c017 	add	x23, x0, #0x30
   2e1c0:	14000013 	b	2e20c <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x104c>
   2e1c4:	f8008420 	str	x0, [x1], #8
   2e1c8:	f94127e2 	ldr	x2, [sp, #584]
   2e1cc:	f940ebe0 	ldr	x0, [sp, #464]
   2e1d0:	f9010be1 	str	x1, [sp, #528]
   2e1d4:	f94123e1 	ldr	x1, [sp, #576]
   2e1d8:	8b140000 	add	x0, x0, x20
   2e1dc:	f900afe0 	str	x0, [sp, #344]
   2e1e0:	eb02003f 	cmp	x1, x2
   2e1e4:	54000380 	b.eq	2e254 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1094>  // b.none
   2e1e8:	f8008420 	str	x0, [x1], #8
   2e1ec:	a95903e2 	ldp	x2, x0, [sp, #400]
   2e1f0:	91000673 	add	x19, x19, #0x1
   2e1f4:	91006294 	add	x20, x20, #0x18
   2e1f8:	f90123e1 	str	x1, [sp, #576]
   2e1fc:	cb020000 	sub	x0, x0, x2
   2e200:	eb800a7f 	cmp	x19, x0, asr #2
   2e204:	540003a2 	b.cs	2e278 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x10b8>  // b.hs, b.nlast
   2e208:	f9410be1 	ldr	x1, [sp, #528]
   2e20c:	b8737840 	ldr	w0, [x2, x19, lsl #2]
   2e210:	f940b3e3 	ldr	x3, [sp, #352]
   2e214:	f9410fe2 	ldr	x2, [sp, #536]
   2e218:	9b350c00 	smaddl	x0, w0, w21, x3
   2e21c:	9100c000 	add	x0, x0, #0x30
   2e220:	f900afe0 	str	x0, [sp, #344]
   2e224:	eb01005f 	cmp	x2, x1
   2e228:	54fffce1 	b.ne	2e1c4 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1004>  // b.any
   2e22c:	f94057e0 	ldr	x0, [sp, #168]
   2e230:	aa1603e2 	mov	x2, x22
   2e234:	97fffb4b 	bl	2cf60 <void std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> > const*, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > const*> >::_M_realloc_insert<std::vector<float, lqcd_native::WorkspaceAllocator<float> > const*>(__gnu_cxx::__normal_iterator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > const**, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> > const*, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > const*> > >, std::vector<float, lqcd_native::WorkspaceAllocator<float> > const*&&)>
   2e238:	f940ebe0 	ldr	x0, [sp, #464]
   2e23c:	f94123e1 	ldr	x1, [sp, #576]
   2e240:	f94127e2 	ldr	x2, [sp, #584]
   2e244:	8b140000 	add	x0, x0, x20
   2e248:	f900afe0 	str	x0, [sp, #344]
   2e24c:	eb02003f 	cmp	x1, x2
   2e250:	54fffcc1 	b.ne	2e1e8 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1028>  // b.any
   2e254:	aa1603e2 	mov	x2, x22
   2e258:	aa1703e0 	mov	x0, x23
   2e25c:	97fffb8d 	bl	2d090 <void std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >*, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> >*> >::_M_realloc_insert<std::vector<float, lqcd_native::WorkspaceAllocator<float> >*>(__gnu_cxx::__normal_iterator<std::vector<float, lqcd_native::WorkspaceAllocator<float> >**, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >*, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> >*> > >, std::vector<float, lqcd_native::WorkspaceAllocator<float> >*&&)>
   2e260:	a95903e2 	ldp	x2, x0, [sp, #400]
   2e264:	91000673 	add	x19, x19, #0x1
   2e268:	91006294 	add	x20, x20, #0x18
   2e26c:	cb020000 	sub	x0, x0, x2
   2e270:	eb800a7f 	cmp	x19, x0, asr #2
   2e274:	54fffca3 	b.cc	2e208 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1048>  // b.lo, b.ul, b.last
   2e278:	f94057e0 	ldr	x0, [sp, #168]
   2e27c:	9100c002 	add	x2, x0, #0x30
   2e280:	aa0003e1 	mov	x1, x0
   2e284:	aa1b03e0 	mov	x0, x27
   2e288:	94000c36 	bl	31360 <NativeMG::Impl::coarse_schur_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> > const*, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > const*> > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >*, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> >*> > const&) const>
   2e28c:	a95903e1 	ldp	x1, x0, [sp, #400]
   2e290:	d2800014 	mov	x20, #0x0                   	// #0
   2e294:	d2800013 	mov	x19, #0x0                   	// #0
   2e298:	52801916 	mov	w22, #0xc8                  	// #200
   2e29c:	1e7e1008 	fmov	d8, #-1.000000000000000000e+00
   2e2a0:	eb01001f 	cmp	x0, x1
   2e2a4:	54000260 	b.eq	2e2f0 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1130>  // b.none
   2e2a8:	b8737821 	ldr	w1, [x1, x19, lsl #2]
   2e2ac:	f940b3e0 	ldr	x0, [sp, #352]
   2e2b0:	9b360021 	smaddl	x1, w1, w22, x0
   2e2b4:	91006035 	add	x21, x1, #0x18
   2e2b8:	aa1503e0 	mov	x0, x21
   2e2bc:	97ffe17d 	bl	268b0 <std::vector<float, lqcd_native::WorkspaceAllocator<float> >::operator=(std::vector<float, lqcd_native::WorkspaceAllocator<float> > const&) [clone .isra.0]>
   2e2c0:	f940ebe1 	ldr	x1, [sp, #464]
   2e2c4:	aa1503e0 	mov	x0, x21
   2e2c8:	1e604100 	fmov	d0, d8
   2e2cc:	2f00e401 	movi	d1, #0x0
   2e2d0:	8b140021 	add	x1, x1, x20
   2e2d4:	97ff7d2b 	bl	d780 <lqcd_native::detail::coarse_axpy(std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::complex<double>, std::vector<float, lqcd_native::WorkspaceAllocator<float> > const&)>
   2e2d8:	a95903e1 	ldp	x1, x0, [sp, #400]
   2e2dc:	91000673 	add	x19, x19, #0x1
   2e2e0:	91006294 	add	x20, x20, #0x18
   2e2e4:	cb010000 	sub	x0, x0, x1
   2e2e8:	eb800a7f 	cmp	x19, x0, asr #2
   2e2ec:	54fffde3 	b.cc	2e2a8 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x10e8>  // b.lo, b.ul, b.last
   2e2f0:	a95d53f3 	ldp	x19, x20, [sp, #464]
   2e2f4:	eb14027f 	cmp	x19, x20
   2e2f8:	54000120 	b.eq	2e31c <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x115c>  // b.none
   2e2fc:	d503201f 	nop
   2e300:	f9400260 	ldr	x0, [x19]
   2e304:	91006273 	add	x19, x19, #0x18
   2e308:	b4002fa0 	cbz	x0, 2e8fc <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x173c>
   2e30c:	97ff5b65 	bl	50a0 <free@plt>
   2e310:	eb14027f 	cmp	x19, x20
   2e314:	54ffff61 	b.ne	2e300 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1140>  // b.any
   2e318:	f940ebf4 	ldr	x20, [sp, #464]
   2e31c:	b40000b4 	cbz	x20, 2e330 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1170>
   2e320:	f940f3e1 	ldr	x1, [sp, #480]
   2e324:	aa1403e0 	mov	x0, x20
   2e328:	cb140021 	sub	x1, x1, x20
   2e32c:	97ff5bd1 	bl	5270 <operator delete(void*, unsigned long)@plt>
   2e330:	f94047e0 	ldr	x0, [sp, #136]
   2e334:	f9406fe1 	ldr	x1, [sp, #216]
   2e338:	eb01001f 	cmp	x0, x1
   2e33c:	54000080 	b.eq	2e34c <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x118c>  // b.none
   2e340:	f94063e2 	ldr	x2, [sp, #192]
   2e344:	52800001 	mov	w1, #0x0                   	// #0
   2e348:	97ff5b5e 	bl	50c0 <memset@plt>
   2e34c:	a9594ff6 	ldp	x22, x19, [sp, #400]
   2e350:	eb16027f 	cmp	x19, x22
   2e354:	54000360 	b.eq	2e3c0 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1200>  // b.none
   2e358:	f94047f9 	ldr	x25, [sp, #136]
   2e35c:	d0ffffb5 	adrp	x21, 24000 <(anonymous namespace)::coarse_gcr_fused_step(std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&, double&) [clone ._omp_fn.1]+0x90>
   2e360:	910743f7 	add	x23, sp, #0x1d0
   2e364:	2f00e408 	movi	d8, #0x0
   2e368:	912c42b5 	add	x21, x21, #0xb10
   2e36c:	52801914 	mov	w20, #0xc8                  	// #200
   2e370:	b84046da 	ldr	w26, [x22], #4
   2e374:	f940b3e2 	ldr	x2, [sp, #352]
   2e378:	52800003 	mov	w3, #0x0                   	// #0
   2e37c:	aa1703e1 	mov	x1, x23
   2e380:	aa1503e0 	mov	x0, x21
   2e384:	9b340b42 	smaddl	x2, w26, w20, x2
   2e388:	91006044 	add	x4, x2, #0x18
   2e38c:	a9418845 	ldp	x5, x2, [x2, #24]
   2e390:	fd00efe8 	str	d8, [sp, #472]
   2e394:	f900ebe4 	str	x4, [sp, #464]
   2e398:	d2835004 	mov	x4, #0x1a80                	// #6784
   2e39c:	f2a000c4 	movk	x4, #0x6, lsl #16
   2e3a0:	cb050042 	sub	x2, x2, x5
   2e3a4:	eb04005f 	cmp	x2, x4
   2e3a8:	1a9f87e2 	cset	w2, ls  // ls = plast
   2e3ac:	97ff5c71 	bl	5570 <GOMP_parallel@plt>
   2e3b0:	fd40efe0 	ldr	d0, [sp, #472]
   2e3b4:	fc3adb20 	str	d0, [x25, w26, sxtw #3]
   2e3b8:	eb16027f 	cmp	x19, x22
   2e3bc:	54fffda1 	b.ne	2e370 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x11b0>  // b.any
   2e3c0:	f9404be0 	ldr	x0, [sp, #144]
   2e3c4:	f9475800 	ldr	x0, [x0, #3760]
   2e3c8:	b9400000 	ldr	w0, [x0]
   2e3cc:	7100041f 	cmp	w0, #0x1
   2e3d0:	540029ec 	b.gt	2e90c <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x174c>
   2e3d4:	b9414fe0 	ldr	w0, [sp, #332]
   2e3d8:	a9595ff4 	ldp	x20, x23, [sp, #400]
   2e3dc:	11000400 	add	w0, w0, #0x1
   2e3e0:	b9014fe0 	str	w0, [sp, #332]
   2e3e4:	eb1402ff 	cmp	x23, x20
   2e3e8:	540005a0 	b.eq	2e49c <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x12dc>  // b.none
   2e3ec:	f94047f6 	ldr	x22, [sp, #136]
   2e3f0:	52801919 	mov	w25, #0xc8                  	// #200
   2e3f4:	f90043f8 	str	x24, [sp, #128]
   2e3f8:	b9400295 	ldr	w21, [x20]
   2e3fc:	f940b3e0 	ldr	x0, [sp, #352]
   2e400:	fc75dac0 	ldr	d0, [x22, w21, sxtw #3]
   2e404:	9b3902b5 	smaddl	x21, w21, w25, x0
   2e408:	1e602008 	fcmp	d0, #0.0
   2e40c:	54002745 	b.pl	2e8f4 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1734>  // b.nfrst
   2e410:	97ff5cfc 	bl	5800 <sqrt@plt>
   2e414:	d503201f 	nop
   2e418:	f9404aba 	ldr	x26, [x21, #144]
   2e41c:	f9404eb8 	ldr	x24, [x21, #152]
   2e420:	910242bc 	add	x28, x21, #0x90
   2e424:	fd005aa0 	str	d0, [x21, #176]
   2e428:	eb18035f 	cmp	x26, x24
   2e42c:	54000140 	b.eq	2e454 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1294>  // b.none
   2e430:	aa1a03f3 	mov	x19, x26
   2e434:	d503201f 	nop
   2e438:	f9400260 	ldr	x0, [x19]
   2e43c:	91006273 	add	x19, x19, #0x18
   2e440:	b40024e0 	cbz	x0, 2e8dc <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x171c>
   2e444:	97ff5b17 	bl	50a0 <free@plt>
   2e448:	eb18027f 	cmp	x19, x24
   2e44c:	54ffff61 	b.ne	2e438 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1278>  // b.any
   2e450:	f900079a 	str	x26, [x28, #8]
   2e454:	9101e2ba 	add	x26, x21, #0x78
   2e458:	f940075c 	ldr	x28, [x26, #8]
   2e45c:	f9403eb5 	ldr	x21, [x21, #120]
   2e460:	eb1c02bf 	cmp	x21, x28
   2e464:	54000140 	b.eq	2e48c <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x12cc>  // b.none
   2e468:	aa1503f3 	mov	x19, x21
   2e46c:	d503201f 	nop
   2e470:	f9400260 	ldr	x0, [x19]
   2e474:	91006273 	add	x19, x19, #0x18
   2e478:	b4002380 	cbz	x0, 2e8e8 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1728>
   2e47c:	97ff5b09 	bl	50a0 <free@plt>
   2e480:	eb13039f 	cmp	x28, x19
   2e484:	54ffff61 	b.ne	2e470 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x12b0>  // b.any
   2e488:	f9000755 	str	x21, [x26, #8]
   2e48c:	91001294 	add	x20, x20, #0x4
   2e490:	eb17029f 	cmp	x20, x23
   2e494:	54fffb21 	b.ne	2e3f8 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1238>  // b.any
   2e498:	f94043f8 	ldr	x24, [sp, #128]
   2e49c:	b94103e1 	ldr	w1, [sp, #256]
   2e4a0:	b94b6360 	ldr	w0, [x27, #2912]
   2e4a4:	b9413ffc 	ldr	w28, [sp, #316]
   2e4a8:	11000421 	add	w1, w1, #0x1
   2e4ac:	b90103e1 	str	w1, [sp, #256]
   2e4b0:	6b01001f 	cmp	w0, w1
   2e4b4:	54ffa9ec 	b.gt	2d9f0 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x830>
   2e4b8:	f94107e2 	ldr	x2, [sp, #520]
   2e4bc:	f9410be0 	ldr	x0, [sp, #528]
   2e4c0:	eb00005f 	cmp	x2, x0
   2e4c4:	54000040 	b.eq	2e4cc <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x130c>  // b.none
   2e4c8:	f9010be2 	str	x2, [sp, #528]
   2e4cc:	f94113e0 	ldr	x0, [sp, #544]
   2e4d0:	f94117e1 	ldr	x1, [sp, #552]
   2e4d4:	eb01001f 	cmp	x0, x1
   2e4d8:	54000040 	b.eq	2e4e0 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1320>  // b.none
   2e4dc:	f90117e0 	str	x0, [sp, #552]
   2e4e0:	f9411fe0 	ldr	x0, [sp, #568]
   2e4e4:	f94123e1 	ldr	x1, [sp, #576]
   2e4e8:	eb01001f 	cmp	x0, x1
   2e4ec:	54000040 	b.eq	2e4f4 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1334>  // b.none
   2e4f0:	f90123e0 	str	x0, [sp, #576]
   2e4f4:	d2800014 	mov	x20, #0x0                   	// #0
   2e4f8:	d2800013 	mov	x19, #0x0                   	// #0
   2e4fc:	7100039f 	cmp	w28, #0x0
   2e500:	540021ed 	b.le	2e93c <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x177c>
   2e504:	f9404fe1 	ldr	x1, [sp, #152]
   2e508:	f94057e0 	ldr	x0, [sp, #168]
   2e50c:	910743f6 	add	x22, sp, #0x1d0
   2e510:	f94067e2 	ldr	x2, [sp, #200]
   2e514:	cb180037 	sub	x23, x1, x24
   2e518:	f94073e1 	ldr	x1, [sp, #224]
   2e51c:	9100c01a 	add	x26, x0, #0x30
   2e520:	91006000 	add	x0, x0, #0x18
   2e524:	f90043e0 	str	x0, [sp, #128]
   2e528:	cb020039 	sub	x25, x1, x2
   2e52c:	14000005 	b	2e540 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1380>
   2e530:	91000673 	add	x19, x19, #0x1
   2e534:	91032294 	add	x20, x20, #0xc8
   2e538:	6b13039f 	cmp	w28, w19
   2e53c:	5400200d 	b.le	2e93c <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x177c>
   2e540:	f940b3e0 	ldr	x0, [sp, #352]
   2e544:	8b140000 	add	x0, x0, x20
   2e548:	fd405400 	ldr	d0, [x0, #168]
   2e54c:	1e602008 	fcmp	d0, #0.0
   2e550:	54ffff00 	b.eq	2e530 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1370>  // b.none
   2e554:	f9405be1 	ldr	x1, [sp, #176]
   2e558:	8b130675 	add	x21, x19, x19, lsl #1
   2e55c:	f9410fe3 	ldr	x3, [sp, #536]
   2e560:	d37df2b5 	lsl	x21, x21, #3
   2e564:	f9400022 	ldr	x2, [x1]
   2e568:	f9410be1 	ldr	x1, [sp, #528]
   2e56c:	8b150042 	add	x2, x2, x21
   2e570:	f900ebe2 	str	x2, [sp, #464]
   2e574:	eb03003f 	cmp	x1, x3
   2e578:	54003220 	b.eq	2ebbc <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x19fc>  // b.none
   2e57c:	f8008422 	str	x2, [x1], #8
   2e580:	f9010be1 	str	x1, [sp, #528]
   2e584:	f94117e1 	ldr	x1, [sp, #552]
   2e588:	f9411be2 	ldr	x2, [sp, #560]
   2e58c:	9100c000 	add	x0, x0, #0x30
   2e590:	f900ebe0 	str	x0, [sp, #464]
   2e594:	eb02003f 	cmp	x1, x2
   2e598:	54003060 	b.eq	2eba4 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x19e4>  // b.none
   2e59c:	f8008420 	str	x0, [x1], #8
   2e5a0:	f90117e1 	str	x1, [sp, #552]
   2e5a4:	f9405fe0 	ldr	x0, [sp, #184]
   2e5a8:	f94123e1 	ldr	x1, [sp, #576]
   2e5ac:	f94127e2 	ldr	x2, [sp, #584]
   2e5b0:	f9400000 	ldr	x0, [x0]
   2e5b4:	8b150000 	add	x0, x0, x21
   2e5b8:	f900ebe0 	str	x0, [sp, #464]
   2e5bc:	eb02003f 	cmp	x1, x2
   2e5c0:	54002e40 	b.eq	2eb88 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x19c8>  // b.none
   2e5c4:	f8008420 	str	x0, [x1], #8
   2e5c8:	b9413ffc 	ldr	w28, [sp, #316]
   2e5cc:	f90123e1 	str	x1, [sp, #576]
   2e5d0:	17ffffd8 	b	2e530 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1370>
   2e5d4:	f9400c65 	ldr	x5, [x3, #24]
   2e5d8:	f9401062 	ldr	x2, [x3, #32]
   2e5dc:	91006064 	add	x4, x3, #0x18
   2e5e0:	aa1703e0 	mov	x0, x23
   2e5e4:	aa1803e1 	mov	x1, x24
   2e5e8:	52800003 	mov	w3, #0x0                   	// #0
   2e5ec:	f900ebe4 	str	x4, [sp, #464]
   2e5f0:	fd00efe8 	str	d8, [sp, #472]
   2e5f4:	910322b5 	add	x21, x21, #0xc8
   2e5f8:	cb050042 	sub	x2, x2, x5
   2e5fc:	eb13005f 	cmp	x2, x19
   2e600:	1a9f87e2 	cset	w2, ls  // ls = plast
   2e604:	97ff5bdb 	bl	5570 <GOMP_parallel@plt>
   2e608:	b9413ff6 	ldr	w22, [sp, #316]
   2e60c:	fd40efe0 	ldr	d0, [sp, #472]
   2e610:	f94047e0 	ldr	x0, [sp, #136]
   2e614:	fc347800 	str	d0, [x0, x20, lsl #3]
   2e618:	91000694 	add	x20, x20, #0x1
   2e61c:	6b1402df 	cmp	w22, w20
   2e620:	54ff922d 	b.le	2d864 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x6a4>
   2e624:	f940b3e2 	ldr	x2, [sp, #352]
   2e628:	17fffc88 	b	2d848 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x688>
   2e62c:	97ff5ab5 	bl	5100 <omp_in_parallel@plt>
   2e630:	7100001f 	cmp	w0, #0x0
   2e634:	b94107e1 	ldr	w1, [sp, #260]
   2e638:	7a410260 	ccmp	w19, w1, #0x0, eq  // eq = none
   2e63c:	1a9fc7e0 	cset	w0, le
   2e640:	6b01027f 	cmp	w19, w1
   2e644:	1a9f07e1 	cset	w1, ne  // ne = any
   2e648:	6a000020 	ands	w0, w1, w0
   2e64c:	b9013be0 	str	w0, [sp, #312]
   2e650:	54ff6d00 	b.eq	2d3f0 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x230>  // b.none
   2e654:	2a1303e0 	mov	w0, w19
   2e658:	97ff5b22 	bl	52e0 <omp_set_num_threads@plt>
   2e65c:	17fffb66 	b	2d3f4 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x234>
   2e660:	b0000285 	adrp	x5, 7f000 <__FRAME_END__+0x18c0c>
   2e664:	f94047e1 	ldr	x1, [sp, #136]
   2e668:	f9406fe0 	ldr	x0, [sp, #216]
   2e66c:	b0000284 	adrp	x4, 7f000 <__FRAME_END__+0x18c0c>
   2e670:	f94760a5 	ldr	x5, [x5, #3776]
   2e674:	b0000283 	adrp	x3, 7f000 <__FRAME_END__+0x18c0c>
   2e678:	f9474884 	ldr	x4, [x4, #3728]
   2e67c:	f9478063 	ldr	x3, [x3, #3840]
   2e680:	cb010000 	sub	x0, x0, x1
   2e684:	f94000a5 	ldr	x5, [x5]
   2e688:	aa0003e2 	mov	x2, x0
   2e68c:	d2800020 	mov	x0, #0x1                   	// #1
   2e690:	f90063e2 	str	x2, [sp, #192]
   2e694:	d3438842 	ubfx	x2, x2, #3, #32
   2e698:	97ff5b3a 	bl	5380 <MPI_Allreduce@plt>
   2e69c:	b9413fe0 	ldr	w0, [sp, #316]
   2e6a0:	17fffbdb 	b	2d60c <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x44c>
   2e6a4:	b0000285 	adrp	x5, 7f000 <__FRAME_END__+0x18c0c>
   2e6a8:	b0000284 	adrp	x4, 7f000 <__FRAME_END__+0x18c0c>
   2e6ac:	b0000283 	adrp	x3, 7f000 <__FRAME_END__+0x18c0c>
   2e6b0:	f94063e0 	ldr	x0, [sp, #192]
   2e6b4:	f94760a5 	ldr	x5, [x5, #3776]
   2e6b8:	f9474884 	ldr	x4, [x4, #3728]
   2e6bc:	f9478063 	ldr	x3, [x3, #3840]
   2e6c0:	f94047e1 	ldr	x1, [sp, #136]
   2e6c4:	d3438802 	ubfx	x2, x0, #3, #32
   2e6c8:	d2800020 	mov	x0, #0x1                   	// #1
   2e6cc:	f94000a5 	ldr	x5, [x5]
   2e6d0:	97ff5b2c 	bl	5380 <MPI_Allreduce@plt>
   2e6d4:	b9413ff6 	ldr	w22, [sp, #316]
   2e6d8:	17fffc68 	b	2d878 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x6b8>
   2e6dc:	d2800018 	mov	x24, #0x0                   	// #0
   2e6e0:	f9004fff 	str	xzr, [sp, #152]
   2e6e4:	17fffc9d 	b	2d958 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x798>
   2e6e8:	f940c7e1 	ldr	x1, [sp, #392]
   2e6ec:	eb15003f 	cmp	x1, x21
   2e6f0:	54000b40 	b.eq	2e858 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1698>  // b.none
   2e6f4:	b80046a0 	str	w0, [x21], #4
   2e6f8:	f900c3f5 	str	x21, [sp, #384]
   2e6fc:	b940ba60 	ldr	w0, [x19, #184]
   2e700:	395ec761 	ldrb	w1, [x27, #1969]
   2e704:	91006275 	add	x21, x19, #0x18
   2e708:	91012274 	add	x20, x19, #0x48
   2e70c:	11000400 	add	w0, w0, #0x1
   2e710:	b900ba60 	str	w0, [x19, #184]
   2e714:	340000a1 	cbz	w1, 2e728 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1568>
   2e718:	395f6360 	ldrb	w0, [x27, #2008]
   2e71c:	35000060 	cbnz	w0, 2e728 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1568>
   2e720:	aa1b03e0 	mov	x0, x27
   2e724:	97ffe41f 	bl	277a0 <NativeMG::Impl::prepare_coarse_columns() const [clone .part.1]>
   2e728:	f94006a1 	ldr	x1, [x21, #8]
   2e72c:	f9400e63 	ldr	x3, [x19, #24]
   2e730:	aa1603e2 	mov	x2, x22
   2e734:	aa1403e0 	mov	x0, x20
   2e738:	b901d3ff 	str	wzr, [sp, #464]
   2e73c:	cb030021 	sub	x1, x1, x3
   2e740:	9342fc21 	asr	x1, x1, #2
   2e744:	97ffeeff 	bl	2a340 <std::vector<float, lqcd_native::WorkspaceAllocator<float> >::_M_fill_assign(unsigned long, float const&)>
   2e748:	52800024 	mov	w4, #0x1                   	// #1
   2e74c:	52800002 	mov	w2, #0x0                   	// #0
   2e750:	aa1603e1 	mov	x1, x22
   2e754:	a91d53f5 	stp	x21, x20, [sp, #464]
   2e758:	aa1703e0 	mov	x0, x23
   2e75c:	52800003 	mov	w3, #0x0                   	// #0
   2e760:	f900f3fb 	str	x27, [sp, #480]
   2e764:	b901ebff 	str	wzr, [sp, #488]
   2e768:	3907b3e4 	strb	w4, [sp, #492]
   2e76c:	97ff5b81 	bl	5570 <GOMP_parallel@plt>
   2e770:	b9413ffc 	ldr	w28, [sp, #316]
   2e774:	a9490662 	ldp	x2, x1, [x19, #144]
   2e778:	b9415be0 	ldr	w0, [sp, #344]
   2e77c:	f940c3f5 	ldr	x21, [sp, #384]
   2e780:	cb020021 	sub	x1, x1, x2
   2e784:	f94043e2 	ldr	x2, [sp, #128]
   2e788:	9343fc21 	asr	x1, x1, #3
   2e78c:	9b197c21 	mul	x1, x1, x25
   2e790:	eb01005f 	cmp	x2, x1
   2e794:	9a812041 	csel	x1, x2, x1, cs  // cs = hs, nlast
   2e798:	f90043e1 	str	x1, [sp, #128]
   2e79c:	17fffcaf 	b	2da58 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x898>
   2e7a0:	1e61c000 	fsqrt	d0, d0
   2e7a4:	1e6a2010 	fcmpe	d0, d10
   2e7a8:	540002c4 	b.mi	2e800 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1640>  // b.first
   2e7ac:	910182a0 	add	x0, x21, #0x60
   2e7b0:	910122a5 	add	x5, x21, #0x48
   2e7b4:	9100c2a4 	add	x4, x21, #0x30
   2e7b8:	910062b5 	add	x21, x21, #0x18
   2e7bc:	17fffdaf 	b	2de78 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xcb8>
   2e7c0:	1e61c000 	fsqrt	d0, d0
   2e7c4:	9101e260 	add	x0, x19, #0x78
   2e7c8:	a9408801 	ldp	x1, x2, [x0, #8]
   2e7cc:	fd005a60 	str	d0, [x19, #176]
   2e7d0:	eb02003f 	cmp	x1, x2
   2e7d4:	54ffbd21 	b.ne	2df78 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xdb8>  // b.any
   2e7d8:	91012262 	add	x2, x19, #0x48
   2e7dc:	97fff1d5 	bl	2af30 <void std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >::_M_realloc_insert<std::vector<float, lqcd_native::WorkspaceAllocator<float> > >(__gnu_cxx::__normal_iterator<std::vector<float, lqcd_native::WorkspaceAllocator<float> >*, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > >, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&&)>
   2e7e0:	91024260 	add	x0, x19, #0x90
   2e7e4:	a9408801 	ldp	x1, x2, [x0, #8]
   2e7e8:	eb02003f 	cmp	x1, x2
   2e7ec:	54ffbe01 	b.ne	2dfac <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xdec>  // b.any
   2e7f0:	91018262 	add	x2, x19, #0x60
   2e7f4:	97fff1cf 	bl	2af30 <void std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >::_M_realloc_insert<std::vector<float, lqcd_native::WorkspaceAllocator<float> > >(__gnu_cxx::__normal_iterator<std::vector<float, lqcd_native::WorkspaceAllocator<float> >*, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > >, std::vector<float, lqcd_native::WorkspaceAllocator<float> >&&)>
   2e7f8:	f9404e62 	ldr	x2, [x19, #152]
   2e7fc:	17fffdf5 	b	2dfd0 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xe10>
   2e800:	52800020 	mov	w0, #0x1                   	// #1
   2e804:	390312a0 	strb	w0, [x21, #196]
   2e808:	17fffdb3 	b	2ded4 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xd14>
   2e80c:	b0000285 	adrp	x5, 7f000 <__FRAME_END__+0x18c0c>
   2e810:	b0000284 	adrp	x4, 7f000 <__FRAME_END__+0x18c0c>
   2e814:	b0000283 	adrp	x3, 7f000 <__FRAME_END__+0x18c0c>
   2e818:	b940d3e2 	ldr	w2, [sp, #208]
   2e81c:	f94760a5 	ldr	x5, [x5, #3776]
   2e820:	f9474884 	ldr	x4, [x4, #3728]
   2e824:	aa1803e1 	mov	x1, x24
   2e828:	d2800020 	mov	x0, #0x1                   	// #1
   2e82c:	f9478063 	ldr	x3, [x3, #3840]
   2e830:	f94000a5 	ldr	x5, [x5]
   2e834:	97ff5ad3 	bl	5380 <MPI_Allreduce@plt>
   2e838:	b9414fe0 	ldr	w0, [sp, #332]
   2e83c:	a957e7f4 	ldp	x20, x25, [sp, #376]
   2e840:	11000400 	add	w0, w0, #0x1
   2e844:	b9014fe0 	str	w0, [sp, #332]
   2e848:	eb14033f 	cmp	x25, x20
   2e84c:	54ffa121 	b.ne	2dc70 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xab0>  // b.any
   2e850:	aa1403f9 	mov	x25, x20
   2e854:	17fffd27 	b	2dcf0 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xb30>
   2e858:	f9407fe0 	ldr	x0, [sp, #248]
   2e85c:	aa1503e1 	mov	x1, x21
   2e860:	aa1a03e2 	mov	x2, x26
   2e864:	97ff59df 	bl	4fe0 <void std::vector<int, std::allocator<int> >::_M_realloc_insert<int const&>(__gnu_cxx::__normal_iterator<int*, std::vector<int, std::allocator<int> > >, int const&)@plt>
   2e868:	17ffffa5 	b	2e6fc <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x153c>
   2e86c:	b0000285 	adrp	x5, 7f000 <__FRAME_END__+0x18c0c>
   2e870:	b0000284 	adrp	x4, 7f000 <__FRAME_END__+0x18c0c>
   2e874:	b0000283 	adrp	x3, 7f000 <__FRAME_END__+0x18c0c>
   2e878:	b9410be2 	ldr	w2, [sp, #264]
   2e87c:	f94760a5 	ldr	x5, [x5, #3776]
   2e880:	f9474884 	ldr	x4, [x4, #3728]
   2e884:	d2800020 	mov	x0, #0x1                   	// #1
   2e888:	f9478063 	ldr	x3, [x3, #3840]
   2e88c:	f94067e1 	ldr	x1, [sp, #200]
   2e890:	f94000a5 	ldr	x5, [x5]
   2e894:	97ff5abb 	bl	5380 <MPI_Allreduce@plt>
   2e898:	17fffd4c 	b	2ddc8 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xc08>
   2e89c:	b0000285 	adrp	x5, 7f000 <__FRAME_END__+0x18c0c>
   2e8a0:	b0000284 	adrp	x4, 7f000 <__FRAME_END__+0x18c0c>
   2e8a4:	b0000283 	adrp	x3, 7f000 <__FRAME_END__+0x18c0c>
   2e8a8:	b940f3e2 	ldr	w2, [sp, #240]
   2e8ac:	f94760a5 	ldr	x5, [x5, #3776]
   2e8b0:	f9474884 	ldr	x4, [x4, #3728]
   2e8b4:	d2800020 	mov	x0, #0x1                   	// #1
   2e8b8:	f9478063 	ldr	x3, [x3, #3840]
   2e8bc:	f94047e1 	ldr	x1, [sp, #136]
   2e8c0:	f94000a5 	ldr	x5, [x5]
   2e8c4:	97ff5aaf 	bl	5380 <MPI_Allreduce@plt>
   2e8c8:	17fffd8c 	b	2def8 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xd38>
   2e8cc:	f9408be0 	ldr	x0, [sp, #272]
   2e8d0:	aa1703e2 	mov	x2, x23
   2e8d4:	97ff59c3 	bl	4fe0 <void std::vector<int, std::allocator<int> >::_M_realloc_insert<int const&>(__gnu_cxx::__normal_iterator<int*, std::vector<int, std::allocator<int> > >, int const&)@plt>
   2e8d8:	17fffd95 	b	2df2c <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xd6c>
   2e8dc:	eb13031f 	cmp	x24, x19
   2e8e0:	54ffdac1 	b.ne	2e438 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1278>  // b.any
   2e8e4:	17fffedb 	b	2e450 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1290>
   2e8e8:	eb13039f 	cmp	x28, x19
   2e8ec:	54ffdc21 	b.ne	2e470 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x12b0>  // b.any
   2e8f0:	17fffee6 	b	2e488 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x12c8>
   2e8f4:	1e61c000 	fsqrt	d0, d0
   2e8f8:	17fffec8 	b	2e418 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1258>
   2e8fc:	eb13029f 	cmp	x20, x19
   2e900:	54ffd001 	b.ne	2e300 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1140>  // b.any
   2e904:	f940ebf4 	ldr	x20, [sp, #464]
   2e908:	17fffe85 	b	2e31c <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x115c>
   2e90c:	b0000285 	adrp	x5, 7f000 <__FRAME_END__+0x18c0c>
   2e910:	b0000284 	adrp	x4, 7f000 <__FRAME_END__+0x18c0c>
   2e914:	b0000283 	adrp	x3, 7f000 <__FRAME_END__+0x18c0c>
   2e918:	b940f3e2 	ldr	w2, [sp, #240]
   2e91c:	f94760a5 	ldr	x5, [x5, #3776]
   2e920:	f9474884 	ldr	x4, [x4, #3728]
   2e924:	d2800020 	mov	x0, #0x1                   	// #1
   2e928:	f9478063 	ldr	x3, [x3, #3840]
   2e92c:	f94047e1 	ldr	x1, [sp, #136]
   2e930:	f94000a5 	ldr	x5, [x5]
   2e934:	97ff5a93 	bl	5380 <MPI_Allreduce@plt>
   2e938:	17fffea7 	b	2e3d4 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1214>
   2e93c:	f9404fe4 	ldr	x4, [sp, #152]
   2e940:	f94057e1 	ldr	x1, [sp, #168]
   2e944:	aa1b03e0 	mov	x0, x27
   2e948:	f94067e5 	ldr	x5, [sp, #200]
   2e94c:	cb180084 	sub	x4, x4, x24
   2e950:	9100c023 	add	x3, x1, #0x30
   2e954:	91006022 	add	x2, x1, #0x18
   2e958:	f90053e4 	str	x4, [sp, #160]
   2e95c:	f94073e4 	ldr	x4, [sp, #224]
   2e960:	cb050084 	sub	x4, x4, x5
   2e964:	f90077e4 	str	x4, [sp, #232]
   2e968:	94000d6e 	bl	31f20 <NativeMG::Impl::coarse_reconstruct_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> > const*, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > const*> > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> > const*, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > const*> > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >*, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> >*> > const&) const>
   2e96c:	f9404fe1 	ldr	x1, [sp, #152]
   2e970:	f94067f3 	ldr	x19, [sp, #200]
   2e974:	9106a3e0 	add	x0, sp, #0x1a8
   2e978:	f94073f4 	ldr	x20, [sp, #224]
   2e97c:	cb180021 	sub	x1, x1, x24
   2e980:	f90053e1 	str	x1, [sp, #160]
   2e984:	cb130281 	sub	x1, x20, x19
   2e988:	f90077e1 	str	x1, [sp, #232]
   2e98c:	97ffecad 	bl	29c40 <NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const::{lambda()#3}::operator()() const>
   2e990:	b4000093 	cbz	x19, 2e9a0 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x17e0>
   2e994:	cb130281 	sub	x1, x20, x19
   2e998:	aa1303e0 	mov	x0, x19
   2e99c:	97ff5a35 	bl	5270 <operator delete(void*, unsigned long)@plt>
   2e9a0:	b40000b8 	cbz	x24, 2e9b4 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x17f4>
   2e9a4:	f9404fe0 	ldr	x0, [sp, #152]
   2e9a8:	cb180001 	sub	x1, x0, x24
   2e9ac:	aa1803e0 	mov	x0, x24
   2e9b0:	97ff5a30 	bl	5270 <operator delete(void*, unsigned long)@plt>
   2e9b4:	f940cbe0 	ldr	x0, [sp, #400]
   2e9b8:	b4000080 	cbz	x0, 2e9c8 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1808>
   2e9bc:	f940d3e1 	ldr	x1, [sp, #416]
   2e9c0:	cb000021 	sub	x1, x1, x0
   2e9c4:	97ff5a2b 	bl	5270 <operator delete(void*, unsigned long)@plt>
   2e9c8:	f940bfe0 	ldr	x0, [sp, #376]
   2e9cc:	b4000080 	cbz	x0, 2e9dc <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x181c>
   2e9d0:	f940c7e1 	ldr	x1, [sp, #392]
   2e9d4:	cb000021 	sub	x1, x1, x0
   2e9d8:	97ff5a26 	bl	5270 <operator delete(void*, unsigned long)@plt>
   2e9dc:	f9411fe0 	ldr	x0, [sp, #568]
   2e9e0:	b4000080 	cbz	x0, 2e9f0 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1830>
   2e9e4:	f94127e1 	ldr	x1, [sp, #584]
   2e9e8:	cb000021 	sub	x1, x1, x0
   2e9ec:	97ff5a21 	bl	5270 <operator delete(void*, unsigned long)@plt>
   2e9f0:	f94113e0 	ldr	x0, [sp, #544]
   2e9f4:	b4000080 	cbz	x0, 2ea04 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1844>
   2e9f8:	f9411be1 	ldr	x1, [sp, #560]
   2e9fc:	cb000021 	sub	x1, x1, x0
   2ea00:	97ff5a1c 	bl	5270 <operator delete(void*, unsigned long)@plt>
   2ea04:	f94107e0 	ldr	x0, [sp, #520]
   2ea08:	b4000080 	cbz	x0, 2ea18 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1858>
   2ea0c:	f9410fe1 	ldr	x1, [sp, #536]
   2ea10:	cb000021 	sub	x1, x1, x0
   2ea14:	97ff5a17 	bl	5270 <operator delete(void*, unsigned long)@plt>
   2ea18:	f94047e0 	ldr	x0, [sp, #136]
   2ea1c:	f94063e1 	ldr	x1, [sp, #192]
   2ea20:	97ff5a14 	bl	5270 <operator delete(void*, unsigned long)@plt>
   2ea24:	a9565bf4 	ldp	x20, x22, [sp, #352]
   2ea28:	eb16029f 	cmp	x20, x22
   2ea2c:	54000680 	b.eq	2eafc <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x193c>  // b.none
   2ea30:	a9495693 	ldp	x19, x21, [x20, #144]
   2ea34:	eb15027f 	cmp	x19, x21
   2ea38:	54000120 	b.eq	2ea5c <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x189c>  // b.none
   2ea3c:	d503201f 	nop
   2ea40:	f9400260 	ldr	x0, [x19]
   2ea44:	91006273 	add	x19, x19, #0x18
   2ea48:	b4000760 	cbz	x0, 2eb34 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1974>
   2ea4c:	97ff5995 	bl	50a0 <free@plt>
   2ea50:	eb15027f 	cmp	x19, x21
   2ea54:	54ffff61 	b.ne	2ea40 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1880>  // b.any
   2ea58:	f9404a95 	ldr	x21, [x20, #144]
   2ea5c:	b40000b5 	cbz	x21, 2ea70 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x18b0>
   2ea60:	f9405281 	ldr	x1, [x20, #160]
   2ea64:	aa1503e0 	mov	x0, x21
   2ea68:	cb150021 	sub	x1, x1, x21
   2ea6c:	97ff5a01 	bl	5270 <operator delete(void*, unsigned long)@plt>
   2ea70:	a947d693 	ldp	x19, x21, [x20, #120]
   2ea74:	eb15027f 	cmp	x19, x21
   2ea78:	54000120 	b.eq	2ea9c <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x18dc>  // b.none
   2ea7c:	d503201f 	nop
   2ea80:	f9400260 	ldr	x0, [x19]
   2ea84:	91006273 	add	x19, x19, #0x18
   2ea88:	b40004e0 	cbz	x0, 2eb24 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1964>
   2ea8c:	97ff5985 	bl	50a0 <free@plt>
   2ea90:	eb15027f 	cmp	x19, x21
   2ea94:	54ffff61 	b.ne	2ea80 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x18c0>  // b.any
   2ea98:	f9403e95 	ldr	x21, [x20, #120]
   2ea9c:	b40000b5 	cbz	x21, 2eab0 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x18f0>
   2eaa0:	f9404681 	ldr	x1, [x20, #136]
   2eaa4:	aa1503e0 	mov	x0, x21
   2eaa8:	cb150021 	sub	x1, x1, x21
   2eaac:	97ff59f1 	bl	5270 <operator delete(void*, unsigned long)@plt>
   2eab0:	f9403280 	ldr	x0, [x20, #96]
   2eab4:	b4000040 	cbz	x0, 2eabc <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x18fc>
   2eab8:	97ff597a 	bl	50a0 <free@plt>
   2eabc:	f9402680 	ldr	x0, [x20, #72]
   2eac0:	b4000040 	cbz	x0, 2eac8 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1908>
   2eac4:	97ff5977 	bl	50a0 <free@plt>
   2eac8:	f9401a80 	ldr	x0, [x20, #48]
   2eacc:	b4000040 	cbz	x0, 2ead4 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1914>
   2ead0:	97ff5974 	bl	50a0 <free@plt>
   2ead4:	f9400e80 	ldr	x0, [x20, #24]
   2ead8:	b4000040 	cbz	x0, 2eae0 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1920>
   2eadc:	97ff5971 	bl	50a0 <free@plt>
   2eae0:	f9400280 	ldr	x0, [x20]
   2eae4:	91032294 	add	x20, x20, #0xc8
   2eae8:	b40002e0 	cbz	x0, 2eb44 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1984>
   2eaec:	97ff596d 	bl	50a0 <free@plt>
   2eaf0:	eb16029f 	cmp	x20, x22
   2eaf4:	54fff9e1 	b.ne	2ea30 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1870>  // b.any
   2eaf8:	f940b3f6 	ldr	x22, [sp, #352]
   2eafc:	b40000b6 	cbz	x22, 2eb10 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1950>
   2eb00:	f940bbe1 	ldr	x1, [sp, #368]
   2eb04:	aa1603e0 	mov	x0, x22
   2eb08:	cb160021 	sub	x1, x1, x22
   2eb0c:	97ff59d9 	bl	5270 <operator delete(void*, unsigned long)@plt>
   2eb10:	b9413be0 	ldr	w0, [sp, #312]
   2eb14:	34ff3be0 	cbz	w0, 2d290 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xd0>
   2eb18:	b94107e0 	ldr	w0, [sp, #260]
   2eb1c:	97ff59f1 	bl	52e0 <omp_set_num_threads@plt>
   2eb20:	17fff9dc 	b	2d290 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xd0>
   2eb24:	eb1302bf 	cmp	x21, x19
   2eb28:	54fffac1 	b.ne	2ea80 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x18c0>  // b.any
   2eb2c:	f9403e95 	ldr	x21, [x20, #120]
   2eb30:	17ffffdb 	b	2ea9c <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x18dc>
   2eb34:	eb1302bf 	cmp	x21, x19
   2eb38:	54fff841 	b.ne	2ea40 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1880>  // b.any
   2eb3c:	f9404a95 	ldr	x21, [x20, #144]
   2eb40:	17ffffc7 	b	2ea5c <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x189c>
   2eb44:	eb1402df 	cmp	x22, x20
   2eb48:	54fff741 	b.ne	2ea30 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1870>  // b.any
   2eb4c:	f940b3f6 	ldr	x22, [sp, #352]
   2eb50:	17ffffeb 	b	2eafc <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x193c>
   2eb54:	aa1603e2 	mov	x2, x22
   2eb58:	aa1803e0 	mov	x0, x24
   2eb5c:	f90063f7 	str	x23, [sp, #192]
   2eb60:	97fff94c 	bl	2d090 <void std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >*, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> >*> >::_M_realloc_insert<std::vector<float, lqcd_native::WorkspaceAllocator<float> >*>(__gnu_cxx::__normal_iterator<std::vector<float, lqcd_native::WorkspaceAllocator<float> >**, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >*, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> >*> > >, std::vector<float, lqcd_native::WorkspaceAllocator<float> >*&&)>
   2eb64:	b9413fe0 	ldr	w0, [sp, #316]
   2eb68:	17fffae5 	b	2d6fc <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x53c>
   2eb6c:	f94057e0 	ldr	x0, [sp, #168]
   2eb70:	aa1603e2 	mov	x2, x22
   2eb74:	f90063f7 	str	x23, [sp, #192]
   2eb78:	97fff8fa 	bl	2cf60 <void std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> > const*, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > const*> >::_M_realloc_insert<std::vector<float, lqcd_native::WorkspaceAllocator<float> > const*>(__gnu_cxx::__normal_iterator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > const**, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> > const*, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > const*> > >, std::vector<float, lqcd_native::WorkspaceAllocator<float> > const*&&)>
   2eb7c:	f940b3e2 	ldr	x2, [sp, #352]
   2eb80:	8b130042 	add	x2, x2, x19
   2eb84:	17fffaf1 	b	2d748 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x588>
   2eb88:	aa1603e2 	mov	x2, x22
   2eb8c:	aa1a03e0 	mov	x0, x26
   2eb90:	f90053f7 	str	x23, [sp, #160]
   2eb94:	f90077f9 	str	x25, [sp, #232]
   2eb98:	97fff93e 	bl	2d090 <void std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >*, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> >*> >::_M_realloc_insert<std::vector<float, lqcd_native::WorkspaceAllocator<float> >*>(__gnu_cxx::__normal_iterator<std::vector<float, lqcd_native::WorkspaceAllocator<float> >**, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >*, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> >*> > >, std::vector<float, lqcd_native::WorkspaceAllocator<float> >*&&)>
   2eb9c:	b9413ffc 	ldr	w28, [sp, #316]
   2eba0:	17fffe64 	b	2e530 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1370>
   2eba4:	f94043e0 	ldr	x0, [sp, #128]
   2eba8:	aa1603e2 	mov	x2, x22
   2ebac:	f90053f7 	str	x23, [sp, #160]
   2ebb0:	f90077f9 	str	x25, [sp, #232]
   2ebb4:	97fff8eb 	bl	2cf60 <void std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> > const*, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > const*> >::_M_realloc_insert<std::vector<float, lqcd_native::WorkspaceAllocator<float> > const*>(__gnu_cxx::__normal_iterator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > const**, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> > const*, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > const*> > >, std::vector<float, lqcd_native::WorkspaceAllocator<float> > const*&&)>
   2ebb8:	17fffe7b 	b	2e5a4 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x13e4>
   2ebbc:	f94057e0 	ldr	x0, [sp, #168]
   2ebc0:	aa1603e2 	mov	x2, x22
   2ebc4:	f90053f7 	str	x23, [sp, #160]
   2ebc8:	f90077f9 	str	x25, [sp, #232]
   2ebcc:	97fff8e5 	bl	2cf60 <void std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> > const*, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > const*> >::_M_realloc_insert<std::vector<float, lqcd_native::WorkspaceAllocator<float> > const*>(__gnu_cxx::__normal_iterator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > const**, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> > const*, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > const*> > >, std::vector<float, lqcd_native::WorkspaceAllocator<float> > const*&&)>
   2ebd0:	f940b3e0 	ldr	x0, [sp, #352]
   2ebd4:	8b140000 	add	x0, x0, x20
   2ebd8:	17fffe6b 	b	2e584 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x13c4>
   2ebdc:	f90067ff 	str	xzr, [sp, #200]
   2ebe0:	f90073ff 	str	xzr, [sp, #224]
   2ebe4:	17fffb6f 	b	2d9a0 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x7e0>
   2ebe8:	aa1303e5 	mov	x5, x19
   2ebec:	17fffd38 	b	2e0cc <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xf0c>
   2ebf0:	d2800014 	mov	x20, #0x0                   	// #0
   2ebf4:	f900ebff 	str	xzr, [sp, #464]
   2ebf8:	f900f3ff 	str	xzr, [sp, #480]
   2ebfc:	17fffd5e 	b	2e174 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xfb4>
   2ec00:	910583e3 	add	x3, sp, #0x160
   2ec04:	9104f3e2 	add	x2, sp, #0x13c
   2ec08:	910533e1 	add	x1, sp, #0x14c
   2ec0c:	f90047ff 	str	xzr, [sp, #136]
   2ec10:	910543e0 	add	x0, sp, #0x150
   2ec14:	f9006fff 	str	xzr, [sp, #216]
   2ec18:	f9008fe3 	str	x3, [sp, #280]
   2ec1c:	b9014fff 	str	wzr, [sp, #332]
   2ec20:	a9167fff 	stp	xzr, xzr, [sp, #352]
   2ec24:	f900bbff 	str	xzr, [sp, #368]
   2ec28:	a91aefe2 	stp	x2, x27, [sp, #424]
   2ec2c:	a91b8fe1 	stp	x1, x3, [sp, #440]
   2ec30:	f900e7e0 	str	x0, [sp, #456]
   2ec34:	b0000280 	adrp	x0, 7f000 <__FRAME_END__+0x18c0c>
   2ec38:	f9004be0 	str	x0, [sp, #144]
   2ec3c:	f9475800 	ldr	x0, [x0, #3760]
   2ec40:	b9400000 	ldr	w0, [x0]
   2ec44:	7100041f 	cmp	w0, #0x1
   2ec48:	54ffd0cc 	b.gt	2e660 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x14a0>
   2ec4c:	b9414fe0 	ldr	w0, [sp, #332]
   2ec50:	11000400 	add	w0, w0, #0x1
   2ec54:	b9014fe0 	str	w0, [sp, #332]
   2ec58:	f94047e2 	ldr	x2, [sp, #136]
   2ec5c:	f9406fe1 	ldr	x1, [sp, #216]
   2ec60:	9106a3e0 	add	x0, sp, #0x1a8
   2ec64:	cb020021 	sub	x1, x1, x2
   2ec68:	f90063e1 	str	x1, [sp, #192]
   2ec6c:	97ffebf5 	bl	29c40 <NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const::{lambda()#3}::operator()() const>
   2ec70:	f94047e0 	ldr	x0, [sp, #136]
   2ec74:	b4000080 	cbz	x0, 2ec84 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1ac4>
   2ec78:	f9406fe1 	ldr	x1, [sp, #216]
   2ec7c:	cb000021 	sub	x1, x1, x0
   2ec80:	97ff597c 	bl	5270 <operator delete(void*, unsigned long)@plt>
   2ec84:	a9565bf4 	ldp	x20, x22, [sp, #352]
   2ec88:	eb16029f 	cmp	x20, x22
   2ec8c:	54fff380 	b.eq	2eafc <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x193c>  // b.none
   2ec90:	a9495693 	ldp	x19, x21, [x20, #144]
   2ec94:	eb15027f 	cmp	x19, x21
   2ec98:	54000120 	b.eq	2ecbc <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1afc>  // b.none
   2ec9c:	d503201f 	nop
   2eca0:	f9400260 	ldr	x0, [x19]
   2eca4:	91006273 	add	x19, x19, #0x18
   2eca8:	b40005c0 	cbz	x0, 2ed60 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1ba0>
   2ecac:	97ff58fd 	bl	50a0 <free@plt>
   2ecb0:	eb15027f 	cmp	x19, x21
   2ecb4:	54ffff61 	b.ne	2eca0 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1ae0>  // b.any
   2ecb8:	f9404a95 	ldr	x21, [x20, #144]
   2ecbc:	b40000b5 	cbz	x21, 2ecd0 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1b10>
   2ecc0:	f9405281 	ldr	x1, [x20, #160]
   2ecc4:	aa1503e0 	mov	x0, x21
   2ecc8:	cb150021 	sub	x1, x1, x21
   2eccc:	97ff5969 	bl	5270 <operator delete(void*, unsigned long)@plt>
   2ecd0:	a947d693 	ldp	x19, x21, [x20, #120]
   2ecd4:	eb15027f 	cmp	x19, x21
   2ecd8:	54000120 	b.eq	2ecfc <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1b3c>  // b.none
   2ecdc:	d503201f 	nop
   2ece0:	f9400260 	ldr	x0, [x19]
   2ece4:	91006273 	add	x19, x19, #0x18
   2ece8:	b4000440 	cbz	x0, 2ed70 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1bb0>
   2ecec:	97ff58ed 	bl	50a0 <free@plt>
   2ecf0:	eb15027f 	cmp	x19, x21
   2ecf4:	54ffff61 	b.ne	2ece0 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1b20>  // b.any
   2ecf8:	f9403e95 	ldr	x21, [x20, #120]
   2ecfc:	b40000b5 	cbz	x21, 2ed10 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1b50>
   2ed00:	f9404681 	ldr	x1, [x20, #136]
   2ed04:	aa1503e0 	mov	x0, x21
   2ed08:	cb150021 	sub	x1, x1, x21
   2ed0c:	97ff5959 	bl	5270 <operator delete(void*, unsigned long)@plt>
   2ed10:	f9403280 	ldr	x0, [x20, #96]
   2ed14:	b4000040 	cbz	x0, 2ed1c <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1b5c>
   2ed18:	97ff58e2 	bl	50a0 <free@plt>
   2ed1c:	f9402680 	ldr	x0, [x20, #72]
   2ed20:	b4000040 	cbz	x0, 2ed28 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1b68>
   2ed24:	97ff58df 	bl	50a0 <free@plt>
   2ed28:	f9401a80 	ldr	x0, [x20, #48]
   2ed2c:	b4000040 	cbz	x0, 2ed34 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1b74>
   2ed30:	97ff58dc 	bl	50a0 <free@plt>
   2ed34:	f9400e80 	ldr	x0, [x20, #24]
   2ed38:	b4000040 	cbz	x0, 2ed40 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1b80>
   2ed3c:	97ff58d9 	bl	50a0 <free@plt>
   2ed40:	f9400280 	ldr	x0, [x20]
   2ed44:	91032294 	add	x20, x20, #0xc8
   2ed48:	b40001c0 	cbz	x0, 2ed80 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1bc0>
   2ed4c:	97ff58d5 	bl	50a0 <free@plt>
   2ed50:	eb16029f 	cmp	x20, x22
   2ed54:	54fff9e1 	b.ne	2ec90 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1ad0>  // b.any
   2ed58:	f940b3f6 	ldr	x22, [sp, #352]
   2ed5c:	17ffff68 	b	2eafc <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x193c>
   2ed60:	eb1302bf 	cmp	x21, x19
   2ed64:	54fff9e1 	b.ne	2eca0 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1ae0>  // b.any
   2ed68:	f9404a95 	ldr	x21, [x20, #144]
   2ed6c:	17ffffd4 	b	2ecbc <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1afc>
   2ed70:	eb1302bf 	cmp	x21, x19
   2ed74:	54fffb61 	b.ne	2ece0 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1b20>  // b.any
   2ed78:	f9403e95 	ldr	x21, [x20, #120]
   2ed7c:	17ffffe0 	b	2ecfc <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1b3c>
   2ed80:	eb1402df 	cmp	x22, x20
   2ed84:	54fff861 	b.ne	2ec90 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1ad0>  // b.any
   2ed88:	f940b3f6 	ldr	x22, [sp, #352]
   2ed8c:	17ffff5c 	b	2eafc <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x193c>
   2ed90:	f90047ff 	str	xzr, [sp, #136]
   2ed94:	f9006fff 	str	xzr, [sp, #216]
   2ed98:	17fff9d7 	b	2d4f4 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x334>
   2ed9c:	f94047e0 	ldr	x0, [sp, #136]
   2eda0:	f9406fe1 	ldr	x1, [sp, #216]
   2eda4:	eb01001f 	cmp	x0, x1
   2eda8:	54ff52c1 	b.ne	2d800 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x640>  // b.any
   2edac:	f90063ff 	str	xzr, [sp, #192]
   2edb0:	f9404be0 	ldr	x0, [sp, #144]
   2edb4:	f9475800 	ldr	x0, [x0, #3760]
   2edb8:	b9400000 	ldr	w0, [x0]
   2edbc:	7100041f 	cmp	w0, #0x1
   2edc0:	54ffc72c 	b.gt	2e6a4 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x14e4>
   2edc4:	b9414fe0 	ldr	w0, [sp, #332]
   2edc8:	11000400 	add	w0, w0, #0x1
   2edcc:	b9014fe0 	str	w0, [sp, #332]
   2edd0:	17fffac3 	b	2d8dc <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x71c>
   2edd4:	f90063ff 	str	xzr, [sp, #192]
   2edd8:	17fffa91 	b	2d81c <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x65c>
   2eddc:	f0000160 	adrp	x0, 5d000 <_fini+0x34>
   2ede0:	9117c000 	add	x0, x0, #0x5f0
   2ede4:	97ff58a3 	bl	5070 <std::__throw_length_error(char const*)@plt>
   2ede8:	f0000160 	adrp	x0, 5d000 <_fini+0x34>
   2edec:	9117c000 	add	x0, x0, #0x5f0
   2edf0:	97ff58a0 	bl	5070 <std::__throw_length_error(char const*)@plt>
   2edf4:	f0000160 	adrp	x0, 5d000 <_fini+0x34>
   2edf8:	9117c000 	add	x0, x0, #0x5f0
   2edfc:	97ff589d 	bl	5070 <std::__throw_length_error(char const*)@plt>
   2ee00:	97ff5970 	bl	53c0 <std::__throw_bad_cast()@plt>
   2ee04:	1e61c000 	fsqrt	d0, d0
   2ee08:	17fffc1c 	b	2de78 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xcb8>
   2ee0c:	f0000160 	adrp	x0, 5d000 <_fini+0x34>
   2ee10:	9117c000 	add	x0, x0, #0x5f0
   2ee14:	97ff5897 	bl	5070 <std::__throw_length_error(char const*)@plt>
   2ee18:	f0000160 	adrp	x0, 5d000 <_fini+0x34>
   2ee1c:	9117c000 	add	x0, x0, #0x5f0
   2ee20:	97ff5894 	bl	5070 <std::__throw_length_error(char const*)@plt>
   2ee24:	aa0003f3 	mov	x19, x0
   2ee28:	f940cbe0 	ldr	x0, [sp, #400]
   2ee2c:	f940d3e1 	ldr	x1, [sp, #416]
   2ee30:	cb000021 	sub	x1, x1, x0
   2ee34:	b4000040 	cbz	x0, 2ee3c <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1c7c>
   2ee38:	97ff590e 	bl	5270 <operator delete(void*, unsigned long)@plt>
   2ee3c:	f940bfe0 	ldr	x0, [sp, #376]
   2ee40:	f940c7e1 	ldr	x1, [sp, #392]
   2ee44:	cb000021 	sub	x1, x1, x0
   2ee48:	b4000040 	cbz	x0, 2ee50 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1c90>
   2ee4c:	97ff5909 	bl	5270 <operator delete(void*, unsigned long)@plt>
   2ee50:	f9411fe0 	ldr	x0, [sp, #568]
   2ee54:	f94127e1 	ldr	x1, [sp, #584]
   2ee58:	cb000021 	sub	x1, x1, x0
   2ee5c:	b4000040 	cbz	x0, 2ee64 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1ca4>
   2ee60:	97ff5904 	bl	5270 <operator delete(void*, unsigned long)@plt>
   2ee64:	f94113e0 	ldr	x0, [sp, #544]
   2ee68:	f9411be1 	ldr	x1, [sp, #560]
   2ee6c:	cb000021 	sub	x1, x1, x0
   2ee70:	b4000040 	cbz	x0, 2ee78 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1cb8>
   2ee74:	97ff58ff 	bl	5270 <operator delete(void*, unsigned long)@plt>
   2ee78:	f94107e0 	ldr	x0, [sp, #520]
   2ee7c:	f9410fe1 	ldr	x1, [sp, #536]
   2ee80:	cb000021 	sub	x1, x1, x0
   2ee84:	b4000040 	cbz	x0, 2ee8c <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1ccc>
   2ee88:	97ff58fa 	bl	5270 <operator delete(void*, unsigned long)@plt>
   2ee8c:	f94047e0 	ldr	x0, [sp, #136]
   2ee90:	f94063e1 	ldr	x1, [sp, #192]
   2ee94:	97ff58f7 	bl	5270 <operator delete(void*, unsigned long)@plt>
   2ee98:	f9408fe0 	ldr	x0, [sp, #280]
   2ee9c:	97ffef31 	bl	2ab60 <std::vector<NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const::State, std::allocator<NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const::State> >::~vector()>
   2eea0:	b9413be0 	ldr	w0, [sp, #312]
   2eea4:	34000060 	cbz	w0, 2eeb0 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1cf0>
   2eea8:	b94107e0 	ldr	w0, [sp, #260]
   2eeac:	97ff590d 	bl	52e0 <omp_set_num_threads@plt>
   2eeb0:	aa1303e0 	mov	x0, x19
   2eeb4:	97ff5a1b 	bl	5720 <_Unwind_Resume@plt>
   2eeb8:	aa0003f3 	mov	x19, x0
   2eebc:	910743e0 	add	x0, sp, #0x1d0
   2eec0:	97ff9104 	bl	132d0 <std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >::~vector()>
   2eec4:	f94067e0 	ldr	x0, [sp, #200]
   2eec8:	b4000060 	cbz	x0, 2eed4 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1d14>
   2eecc:	f94077e1 	ldr	x1, [sp, #232]
   2eed0:	97ff58e8 	bl	5270 <operator delete(void*, unsigned long)@plt>
   2eed4:	b4fffab8 	cbz	x24, 2ee28 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1c68>
   2eed8:	f94053e1 	ldr	x1, [sp, #160]
   2eedc:	aa1803e0 	mov	x0, x24
   2eee0:	97ff58e4 	bl	5270 <operator delete(void*, unsigned long)@plt>
   2eee4:	17ffffd1 	b	2ee28 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1c68>
   2eee8:	aa0003f3 	mov	x19, x0
   2eeec:	17fffff6 	b	2eec4 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1d04>
   2eef0:	f9404fe1 	ldr	x1, [sp, #152]
   2eef4:	aa0003f3 	mov	x19, x0
   2eef8:	cb180021 	sub	x1, x1, x24
   2eefc:	f90053e1 	str	x1, [sp, #160]
   2ef00:	b5fffed8 	cbnz	x24, 2eed8 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1d18>
   2ef04:	17ffffc9 	b	2ee28 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1c68>
   2ef08:	aa0003f3 	mov	x19, x0
   2ef0c:	17ffffe3 	b	2ee98 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1cd8>
   2ef10:	aa0003f3 	mov	x19, x0
   2ef14:	f94047e0 	ldr	x0, [sp, #136]
   2ef18:	b5fffba0 	cbnz	x0, 2ee8c <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1ccc>
   2ef1c:	17ffffdf 	b	2ee98 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1cd8>
   2ef20:	aa0003f3 	mov	x19, x0
   2ef24:	17ffffcb 	b	2ee50 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1c90>
   2ef28:	aa0003f3 	mov	x19, x0
   2ef2c:	17ffffdd 	b	2eea0 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x1ce0>
