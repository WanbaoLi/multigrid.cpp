
/home/share/nsls_lwb/.cache/mg-opt-20261103/campaign-halo-v2/attempts/000-halo-v2-tests/build/liblqcd_cpu.so.0.2.0:     file format elf64-littleaarch64


Disassembly of section .text:

0000000000029b30 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const>:
   29b30:	a9bc7bfd 	stp	x29, x30, [sp, #-64]!
   29b34:	910003fd 	mov	x29, sp
   29b38:	a90153f3 	stp	x19, x20, [sp, #16]
   29b3c:	f90013f6 	str	x22, [sp, #32]
   29b40:	aa0003f6 	mov	x22, x0
   29b44:	51000460 	sub	w0, w3, #0x1
   29b48:	71002c1f 	cmp	w0, #0xb
   29b4c:	540004c8 	b.hi	29be4 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xb4>  // b.pmore
   29b50:	aa0103f4 	mov	x20, x1
   29b54:	b201f3e0 	mov	x0, #0xaaaaaaaaaaaaaaaa    	// #-6148914691236517206
   29b58:	93407c61 	sxtw	x1, w3
   29b5c:	a9401285 	ldp	x5, x4, [x20]
   29b60:	f2955560 	movk	x0, #0xaaab
   29b64:	cb050084 	sub	x4, x4, x5
   29b68:	9343fc84 	asr	x4, x4, #3
   29b6c:	9b007c84 	mul	x4, x4, x0
   29b70:	eb04003f 	cmp	x1, x4
   29b74:	54000388 	b.hi	29be4 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0xb4>  // b.pmore
   29b78:	a9401045 	ldp	x5, x4, [x2]
   29b7c:	cb050084 	sub	x4, x4, x5
   29b80:	9343fc84 	asr	x4, x4, #3
   29b84:	9b007c84 	mul	x4, x4, x0
   29b88:	eb04003f 	cmp	x1, x4
   29b8c:	540001c8 	b.hi	29bc4 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x94>  // b.pmore
   29b90:	395ecec0 	ldrb	w0, [x22, #1971]
   29b94:	aa1403e1 	mov	x1, x20
   29b98:	340000c0 	cbz	w0, 29bb0 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x80>
   29b9c:	aa1603e0 	mov	x0, x22
   29ba0:	a94153f3 	ldp	x19, x20, [sp, #16]
   29ba4:	f94013f6 	ldr	x22, [sp, #32]
   29ba8:	a8c47bfd 	ldp	x29, x30, [sp], #64
   29bac:	14000d85 	b	2d1c0 <void NativeMG::Impl::coarse_solve_batch_impl<true>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const>
   29bb0:	aa1603e0 	mov	x0, x22
   29bb4:	a94153f3 	ldp	x19, x20, [sp, #16]
   29bb8:	f94013f6 	ldr	x22, [sp, #32]
   29bbc:	a8c47bfd 	ldp	x29, x30, [sp], #64
   29bc0:	14000580 	b	2b1c0 <void NativeMG::Impl::coarse_solve_batch_impl<false>(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const>
   29bc4:	aa0203e0 	mov	x0, x2
   29bc8:	cb040021 	sub	x1, x1, x4
   29bcc:	f9001be2 	str	x2, [sp, #48]
   29bd0:	b9003fe3 	str	w3, [sp, #60]
   29bd4:	940002e3 	bl	2a760 <std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >::_M_default_append(unsigned long)>
   29bd8:	b9403fe3 	ldr	w3, [sp, #60]
   29bdc:	f9401be2 	ldr	x2, [sp, #48]
   29be0:	17ffffec 	b	29b90 <NativeMG::Impl::coarse_solve_batch(std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > > const&, std::vector<std::vector<float, lqcd_native::WorkspaceAllocator<float> >, std::allocator<std::vector<float, lqcd_native::WorkspaceAllocator<float> > > >&, int) const+0x60>
   29be4:	d2800200 	mov	x0, #0x10                  	// #16
   29be8:	97ff6d1a 	bl	5050 <__cxa_allocate_exception@plt>
   29bec:	aa0003f3 	mov	x19, x0
   29bf0:	b00001a1 	adrp	x1, 5e000 <typeinfo name for lqcd::Error+0x9b8>
   29bf4:	91010021 	add	x1, x1, #0x40
   29bf8:	97ff6cfe 	bl	4ff0 <std::runtime_error::runtime_error(char const*)@plt>
   29bfc:	d00002a2 	adrp	x2, 7f000 <__FRAME_END__+0x18c0c>
   29c00:	d00002a1 	adrp	x1, 7f000 <__FRAME_END__+0x18c0c>
   29c04:	aa1303e0 	mov	x0, x19
   29c08:	f9479c42 	ldr	x2, [x2, #3896]
   29c0c:	f947e421 	ldr	x1, [x1, #4040]
   29c10:	97ff6eb0 	bl	56d0 <__cxa_throw@plt>
   29c14:	aa0003e1 	mov	x1, x0
   29c18:	aa1303e0 	mov	x0, x19
   29c1c:	aa0103f3 	mov	x19, x1
   29c20:	97ff6d64 	bl	51b0 <__cxa_free_exception@plt>
   29c24:	aa1303e0 	mov	x0, x19
   29c28:	97ff6ebe 	bl	5720 <_Unwind_Resume@plt>
