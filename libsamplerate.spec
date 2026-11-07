# libsamplerate is used by jackit,
# jackit is used by pulseaudio,
# pulseaudio is used by wine
%ifarch %{x86_64}
%bcond_without compat32
%endif

%bcond_without pgo

# There are packages requiring cmake(samplerate) but we get the cmake
# devel files only when building with cmake: do it for the 64bit builds
# FIXME: Provide a way to do the same for 32bit builds (%%cmake32?)
%bcond_without cmake

%define major 0
%define libname %mklibname samplerate %{major}
%define devname %mklibname samplerate -d
%define lib32name %mklib32name samplerate %{major}
%define dev32name %mklib32name samplerate -d
%global optflags %{optflags} -O3

Summary:	Audio Sample Rate Converter library
Name:		libsamplerate
Version:	0.2.2
Release:	4
License:	GPL-2.0-or-later
Group:		Sound
Url:		https://libsndfile.github.io/libsamplerate/
Source0:	https://github.com/libsndfile/%{name}/releases/download/%{version}/%{name}-%{version}.tar.xz
# From upstream
Patch0:	libsamplerate-0.2.2-CMakeFiles-fixes.patch
Patch1:	libsamplerate-0.2.2-fix-missing-headers.patch
BuildRequires:		autoconf
BuildRequires:		automake
%if %{with cmake}
BuildRequires:		cmake
%endif
BuildRequires:		libtool-base
BuildRequires:		make
BuildRequires:		slibtool
BuildRequires:		pkgconfig(alsa)
BuildRequires:		pkgconfig(fftw3) >= 3
BuildRequires:		pkgconfig(sndfile)
%if %{with compat32}
BuildRequires:		devel(libasound)
BuildRequires:		devel(libfftw3)
BuildRequires:		devel(libsndfile)
%endif

%description
Secret Rabbit Code (aka libsamplerate) is a Sample Rate Converter for audio.
One example of where such a thing would be useful is converting audio from the
CD sample rate of 44.1kHz to the 48kHz sample rate used by DAT players.

SRC is capable of arbitrary and time varying conversions ; from downsampling
by a factor of 12 to upsampling by the same factor. Arbitrary in this case
means that the ratio of input and output sample rates can be an irrational
number. The conversion ratio can also vary with time for speeding up and
slowing down effects.

SRC provides a small set of converters to allow quality to be traded off
against computation cost. The current best converter provides a
signal-to-noise ratio of 97dB with -3dB passband extending from DC to 96%
of the theoretical best bandwidth for a given pair of input and output
sample rates.

#-----------------------------------------------------------------------------

%package -n %{libname}
Summary:	Audio Sample Rate Converter shared library
Group:		System/Libraries

%description -n %{libname}
This package contains the shared library required for running programs
using %{name}.

%files -n %{libname}
%{_libdir}/%{name}.so.%{major}*

#-----------------------------------------------------------------------------

%package -n %{devname}
Summary:	Audio Sample Rate Converter development files
Group:		Development/C
Requires:	%{libname} = %{version}-%{release}

%description -n %{devname}
This package contains the C headers and other files needed to compile
programs with %{name}.

%files -n %{devname}
%{_libdir}/%{name}.so
%if %{with cmake}
%{_libdir}/cmake/SampleRate/*.cmake
%endif
%{_libdir}/pkgconfig/samplerate.pc
%{_includedir}/samplerate.h
%doc AUTHORS ChangeLog
%doc %{_datadir}/doc/%{name}/*

#-----------------------------------------------------------------------------

%if %{with compat32}
%package -n %{lib32name}
Summary:	Audio Sample Rate Converter shared library (32-bit)
Group:	System/Libraries

%description -n %{lib32name}
This package contains the shared library required for running programs
using %{name}.

%files -n %{lib32name}
%{_prefix}/lib/%{name}.so.%{major}*

#-----------------------------------------------------------------------------

%package -n %{dev32name}
Summary:	Audio Sample Rate Converter development files (32-bit)
Group:		Development/C
Requires:	%{devname} = %{version}-%{release}
Requires:	%{lib32name} = %{version}-%{release}

%description -n %{dev32name}
This package contains the C headers and other files needed to compile
programs with %{name}.

%files -n %{dev32name}
%{_prefix}/lib/%{name}.so
%{_prefix}/lib/pkgconfig/samplerate.pc
%endif
# End of compat32

#-----------------------------------------------------------------------------

%prep
%autosetup -p1


%build
%if %{with compat32}
autoreconf -vfi
export CONFIGURE_TOP="$(pwd)"
mkdir build32
pushd build32
	%configure32
	%make_build
popd
%endif

%if %{with cmake}
%cmake -DBUILD_TESTING=ON
%make_build
%else
mkdir build
cd build

%if %{with pgo}
export LD_LIBRARY_PATH="$(pwd)"

CFLAGS="%{optflags} -fprofile-generate -mllvm -vp-counters-per-site=16" \
CXXFLAGS="%{optflags} -fprofile-generate" \
LDFLAGS="%{build_ldflags} -fprofile-generate" \

%configure --disable-static

# Don't use rpath!
sed -i 's|^hardcode_libdir_flag_spec=.*|hardcode_libdir_flag_spec=""|g' libtool
sed -i 's|^runpath_var=LD_RUN_PATH|runpath_var=DIE_RPATH_DIE|g' libtool

%make_build

export LD_LIBRARY_PATH="$(pwd)/src/.libs"
make check

unset LD_LIBRARY_PATH
llvm-profdata merge --output=%{name}-llvm.profdata $(find . -name "*.profraw" -type f)
PROFDATA="$(realpath %{name}-llvm.profdata)"
rm -f *.profraw
make clean

CFLAGS="%{optflags} -fprofile-use=$PROFDATA" \
CXXFLAGS="%{optflags} -fprofile-use=$PROFDATA" \
LDFLAGS="%{build_ldflags} -fprofile-use=$PROFDATA" \
%endif
%configure --disable-static

# Don't use rpath!
sed -i 's|^hardcode_libdir_flag_spec=.*|hardcode_libdir_flag_spec=""|g' libtool
sed -i 's|^runpath_var=LD_RUN_PATH|runpath_var=DIE_RPATH_DIE|g' libtool
%endif


%install
%if %{with compat32}
%make_install -C build32
%endif

%make_install -C build

rm -rf %{buildroot}%{_datadir}/doc/libsamplerate0-dev


%check
%if %{with compat32}
pushd build32
	export LD_LIBRARY_PATH="$(pwd)/src/.libs"
	make check
	unset LD_LIBRARY_PATH
popd
%endif

pushd build
	export LD_LIBRARY_PATH="$(pwd)/src/.libs"
%if %{with cmake}
	make test
%else
	make check
%endif
	unset LD_LIBRARY_PATH

popd
