import { useState } from 'react';
import { Star, Heart, ShoppingCart, ChevronLeft, Minus, Plus } from 'lucide-react';

export default function FigmaNode21790_516517() {
  const [activeTab, setActiveTab] = useState<'description' | 'howToUse' | 'reviews'>('description');
  const [isWishlisted, setIsWishlisted] = useState(false);
  const [currentImageIndex, setCurrentImageIndex] = useState(0);
  const [quantity, setQuantity] = useState(1);

  const productImages = [
    'Main Product Image',
    'Product Detail 1',
    'Product Detail 2',
    'Packaging',
  ];

  const incrementQuantity = () => setQuantity((prev) => prev + 1);
  const decrementQuantity = () => setQuantity((prev) => prev > 1 ? prev - 1 : 1);

  return (
    <div className="min-h-screen bg-gray-50 font-sans">
      {/* Header */}
      <header className="fixed top-0 left-0 right-0 bg-white z-10 border-b border-gray-100">
        <div className="container mx-auto max-w-6xl flex items-center justify-between px-4 py-3">
          <button className="p-2 -ml-2">
            <ChevronLeft size={24} className="text-gray-900" />
          </button>
          <h1 className="text-lg font-semibold text-gray-900">Product Details</h1>
          <button
            onClick={() => setIsWishlisted(!isWishlisted)}
            className={`p-2 -mr-2 ${isWishlisted ? 'text-red-500' : 'text-gray-900'}`}
          >
            <Heart size={24} fill={isWishlisted ? 'currentColor' : 'none'} />
          </button>
        </div>
      </header>

      {/* Main Content */}
      <main className="pt-16 pb-8">
        <div className="container mx-auto max-w-6xl bg-white">
          {/* Breadcrumb */}
          <div className="px-6 py-4 border-b border-gray-100">
            <div className="flex items-center text-sm text-gray-500">
              <span className="hover:text-[#FF7A00] cursor-pointer">Homepage</span>
              <ChevronLeft size={14} className="mx-2 rotate-180" />
              <span className="hover:text-[#FF7A00] cursor-pointer">Flash Sales</span>
              <ChevronLeft size={14} className="mx-2 rotate-180" />
              <span className="text-gray-900 font-medium truncate">Wardah Perfect Bright Brightening Smooth 100ML</span>
            </div>
          </div>

          {/* Product Images + Product Info - Side by Side (Desktop Layout as per Figma) */}
          <div className="px-6 py-8 grid grid-cols-1 lg:grid-cols-2 gap-8">
            {/* Product Images Section */}
            <div className="flex gap-4 items-start">
              {/* Thumbnails - Vertical */}
              <div className="flex flex-col gap-3">
                {productImages.map((_, index) => (
                  <button
                    key={index}
                    onClick={() => setCurrentImageIndex(index)}
                    className={`w-[126px] h-[126px] bg-gray-50 rounded-lg overflow-hidden border-2 transition-all ${
                      index === currentImageIndex
                        ? 'border-[#FF7A00]'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                  >
                    <div className="w-full h-full flex items-center justify-center text-xs text-gray-400">
                      {index + 1}
                    </div>
                  </button>
                ))}
              </div>
              {/* Main Product Image */}
              <div className="flex-1">
                <div className="w-[466px] h-[466px] bg-gray-50 rounded-lg flex items-center justify-center">
                  <div className="text-gray-400">
                    {productImages[currentImageIndex]}
                  </div>
                </div>
              </div>
            </div>

            {/* Product Info Section - Right Side (640px width as per Figma) */}
            <div className="w-[640px] max-w-full">
              {/* Brand & Product Title */}
              <div className="mb-4">
                <p className="text-[#FF7A00] text-lg font-medium mb-1">Wardah</p>
                <h1 className="text-[28px] font-bold text-gray-900 leading-tight">
                  Wardah Perfect Bright Brightening Smooth 100ML
                </h1>
              </div>

              {/* Price */}
              <div className="flex items-baseline gap-3 mb-3">
                <span className="text-[32px] font-bold text-gray-900">IDR 140,000.00</span>
                <span className="text-xl text-gray-400 line-through">IDR 200,000.00</span>
                <span className="bg-red-500 text-white text-sm font-semibold px-3 py-1 rounded">-30%</span>
              </div>

              {/* SKU & Stock Status */}
              <div className="flex items-center justify-between mb-4">
                <p className="text-sm text-gray-500">SKU #3070775</p>
                <span className="text-sm text-green-600 font-medium">In Stock</span>
              </div>

              {/* Rating */}
              <div className="flex items-center gap-2 mb-6">
                <div className="flex items-center gap-1">
                  {[...Array(5)].map((_, i) => (
                    <Star
                      key={i}
                      size={16}
                      fill={i < 5 ? '#FF7A00' : 'none'}
                      className={i < 4.5 ? 'text-[#FF7A00]' : 'text-gray-300'}
                    />
                  ))}
                  <span className="font-medium text-gray-900 ml-1">4.5</span>
                </div>
                <span className="text-sm text-gray-500">(126 reviews)</span>
              </div>

              {/* Quantity Selector */}
              <div className="flex items-center justify-between mb-6">
                <span className="text-base font-medium text-gray-900">Quantity</span>
                <div className="flex items-center gap-3">
                  <button
                    onClick={decrementQuantity}
                    disabled={quantity <= 1}
                    className="w-10 h-10 flex items-center justify-center border border-gray-300 rounded-md hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >
                    <Minus size={18} />
                  </button>
                  <span className="w-12 text-center font-semibold text-gray-900 text-lg">{quantity}</span>
                  <button
                    onClick={incrementQuantity}
                    className="w-10 h-10 flex items-center justify-center border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
                  >
                    <Plus size={18} />
                  </button>
                </div>
              </div>

              {/* Promotions */}
              <div className="space-y-2 mb-8">
                <div className="bg-orange-50 border border-[#FF7A00]/20 rounded-lg px-4 py-3">
                  <p className="text-sm">
                    <span className="font-semibold text-[#FF7A00]">Buy One Get One</span>
                    <span className="text-gray-700"> - Buy each one of Wardah products get one for free (promotion period)</span>
                  </p>
                </div>
                <div className="bg-orange-50 border border-[#FF7A00]/20 rounded-lg px-4 py-3">
                  <p className="text-sm">
                    <span className="font-semibold text-[#FF7A00]">Wardah Item 1 Pc Add Code $50 Off</span>
                    <span className="text-gray-700"> - Buy each 1 of Wardah products for $50 discount (discount code WARDAH100ML) (promotion period)</span>
                  </p>
                </div>
                <div className="bg-orange-50 border border-[#FF7A00]/20 rounded-lg px-4 py-3">
                  <p className="text-sm">
                    <span className="font-semibold text-[#FF7A00]">Buy 1 Item Get $9 coupon</span>
                    <span className="text-gray-700"> - Buy each 1 of Wardah products for $9 Coupon for another purchase (promotion period)</span>
                  </p>
                </div>
              </div>

              {/* Action Buttons - Add to Cart, Save to Wishlist, Flash Buy */}
              <div className="grid grid-cols-2 gap-3 mb-3">
                <button className="flex items-center justify-center gap-2 px-4 py-4 border border-[#FF7A00] text-[#FF7A00] rounded-lg hover:bg-orange-50 transition-colors font-medium">
                  <ShoppingCart size={20} />
                  <span>Add to Cart</span>
                </button>
                <button
                  onClick={() => setIsWishlisted(!isWishlisted)}
                  className={`flex items-center justify-center gap-2 px-4 py-4 border rounded-lg transition-colors font-medium ${
                    isWishlisted
                      ? 'border-red-500 bg-red-50 text-red-500'
                      : 'border-gray-300 text-gray-700 hover:bg-gray-50'
                  }`}
                >
                  <Heart size={20} fill={isWishlisted ? 'currentColor' : 'none'} />
                  <span>Save to wishlist</span>
                </button>
              </div>
              <button className="w-full px-4 py-4 bg-[#FF7A00] hover:bg-[#e66e00] text-white font-semibold rounded-lg transition-colors text-base">
                Flash Buy Now
              </button>
            </div>
          </div>

          {/* Tabs Section - Full Width */}
          <div className="px-6 pb-8">
            {/* Tabs */}
            <div className="border-b border-gray-200">
              <div className="flex gap-0">
                <button
                  onClick={() => setActiveTab('description')}
                  className={`px-6 py-4 text-base font-medium border-b-2 transition-colors ${
                    activeTab === 'description'
                      ? 'border-[#FF7A00] text-[#FF7A00]'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  Description
                </button>
                <button
                  onClick={() => setActiveTab('howToUse')}
                  className={`px-6 py-4 text-base font-medium border-b-2 transition-colors ${
                    activeTab === 'howToUse'
                      ? 'border-[#FF7A00] text-[#FF7A00]'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  How to Use
                </button>
                <button
                  onClick={() => setActiveTab('reviews')}
                  className={`px-6 py-4 text-base font-medium border-b-2 transition-colors ${
                    activeTab === 'reviews'
                      ? 'border-[#FF7A00] text-[#FF7A00]'
                      : 'border-transparent text-gray-500 hover:text-gray-700'
                  }`}
                >
                  Reviews
                </button>
              </div>
            </div>

            {/* Tab Content */}
            <div className="py-8 max-w-4xl">
              {activeTab === 'description' && (
                <div className="space-y-5 text-base text-gray-700 leading-relaxed">
                  <p>
                    Inovasi terbaru dari Wardah, kini hadir foam pencerah yang bersihkan wajah dari kotoran dan debu secara menyeluruh sekaligus melembapkan dan melembutkan kulit untuk wajah tampak cerah, lembut, dan glowing.
                  </p>
                  <p>
                    <strong>4X<sup>^</sup> Bright Berries</strong><br />
                    <sup>^</sup>Kombinasi 4 macam berry (Cranberry, Acai Berry, Goji Berry, & Amethyst Berry) dengan kandungan Vit B3, Vit C, dan Vit E yang formulanya bantu mencerahkan, menutrisi, serta bantu meratakan warna kulit bekas jerawat.
                  </p>
                  <p>
                    <strong>Glow Boost Technology</strong><br />
                    Memberikan kelembapan dan menghaluskan tekstur kulit untuk kulit yang lebih lembut, terasa supple, dan glowing.
                  </p>
                  <div>
                    <strong>Keunggulan:</strong>
                    <ol className="list-decimal pl-5 space-y-1 mt-2">
                      <li>Hypoallergenic</li>
                      <li>Dermatologically Tested</li>
                      <li>Non-comedogenic & Non-Acnegenic</li>
                      <li>0% Alkohol</li>
                      <li>For All Skin Type</li>
                    </ol>
                  </div>
                  <p>
                    Wardah Perfect Bright Creamy Foam Brightening + Smoothing terdiri dari 2 variant :
                    <ol className="list-decimal pl-5 space-y-1 mt-2">
                      <li>Wardah Perfect Bright Creamy Foam Brightening + Smoothing 50 ml</li>
                      <li>Wardah Perfect Bright Creamy Foam Brightening + Smoothing 100 ml</li>
                    </ol>
                  </p>
                </div>
              )}

              {activeTab === 'howToUse' && (
                <div className="space-y-5 text-base text-gray-700 leading-relaxed">
                  <p>
                    Inovasi terbaru dari Wardah, kini hadir foam pencerah yang bersihkan wajah dari kotoran dan debu secara menyeluruh sekaligus angkat minyak berlebih untuk kulit cerah bebas kilap.
                  </p>
                  <p>
                    Perfect Bright Creamy Foam Bright + Oil Control, bersihkan hingga ke pori, bebas kilap, bye bye minyak!
                  </p>
                  <ol className="list-decimal pl-5 space-y-3">
                    <li>Basahi dengan air dan busakan di wajah</li>
                    <li>Pijat lembut dan bilas hingga bersih</li>
                    <li>Hindari daerah mata</li>
                    <li>Untuk hasil optimal, gunakan bersamaan dengan rangkaian Perfect Bright lainnya</li>
                  </ol>
                </div>
              )}

              {activeTab === 'reviews' && (
                <div>
                  <div className="flex items-center justify-between mb-6">
                    <h3 className="font-semibold text-gray-900 text-lg">Reviews</h3>
                    <button className="text-base text-[#FF7A00] font-medium hover:underline">
                      View all
                    </button>
                  </div>
                  <div className="space-y-6">
                    {/* Review 1 */}
                    <div className="border-b border-gray-100 pb-6">
                      <div className="flex items-center justify-between mb-3">
                        <span className="font-medium text-gray-900 text-base">Tim Nguyen</span>
                        <span className="text-sm text-gray-500">1 Jun 2024</span>
                      </div>
                      <div className="flex items-center gap-1 mb-3">
                        {[...Array(5)].map((_, i) => (
                          <Star
                            key={i}
                            size={16}
                            fill={i < 5 ? '#FF7A00' : 'none'}
                            className={i < 5 ? 'text-[#FF7A00]' : 'text-gray-300'}
                          />
                        ))}
                        <span className="text-sm text-gray-500 ml-2">4.5/5</span>
                      </div>
                      <p className="text-base text-gray-700">
                        Alhamduliliah paket udah dateng, pengemasan aman, pengiriman cepat, kurir ramah wah besar sekali 300ml harganya murah, bisa dengan harga yang sangat hemat
                      </p>
                    </div>
                    {/* Review 2 */}
                    <div className="border-b border-gray-100 pb-6">
                      <div className="flex items-center justify-between mb-3">
                        <span className="font-medium text-gray-900 text-base">anois</span>
                        <span className="text-sm text-gray-500">16 May 2024</span>
                      </div>
                      <div className="flex items-center gap-1 mb-3">
                        {[...Array(5)].map((_, i) => (
                          <Star
                            key={i}
                            size={16}
                            fill={i < 4 ? '#FF7A00' : 'none'}
                            className={i < 4 ? 'text-[#FF7A00]' : 'text-gray-300'}
                          />
                        ))}
                        <span className="text-sm text-gray-500 ml-2">4.0/5</span>
                      </div>
                      <p className="text-base text-gray-700">
                        Packaging aman, pesanan cepat sampai, worth it banget untuk di beli dengan harga yang sangat murah dan yang pasti kualitanya murahan
                      </p>
                    </div>
                    {/* Review 3 */}
                    <div className="border-b border-gray-100 pb-6">
                      <div className="flex items-center justify-between mb-3">
                        <span className="font-medium text-gray-900 text-base">rozierai</span>
                        <span className="text-sm text-gray-500">16 May 2024</span>
                      </div>
                      <div className="flex items-center gap-1 mb-3">
                        {[...Array(5)].map((_, i) => (
                          <Star
                            key={i}
                            size={16}
                            fill={i < 4 ? '#FF7A00' : 'none'}
                            className={i < 4 ? 'text-[#FF7A00]' : 'text-gray-300'}
                          />
                        ))}
                        <span className="text-sm text-gray-500 ml-2">4.0/5</span>
                      </div>
                      <p className="text-base text-gray-700">
                        Packaging aman, pesanan cepat sampai, worth it banget untuk di beli dengan harga yang sangat murah dan yang pasti kualitanya murahan
                      </p>
                    </div>
                    {/* Review 4 */}
                    <div className="pb-6">
                      <div className="flex items-center justify-between mb-3">
                        <span className="font-medium text-gray-900 text-base">jlwq07</span>
                        <span className="text-sm text-gray-500">16 May 2024</span>
                      </div>
                      <div className="flex items-center gap-1 mb-3">
                        {[...Array(5)].map((_, i) => (
                          <Star
                            key={i}
                            size={16}
                            fill={i < 4 ? '#FF7A00' : 'none'}
                            className={i < 4 ? 'text-[#FF7A00]' : 'text-gray-300'}
                          />
                        ))}
                        <span className="text-sm text-gray-500 ml-2">4.0/5</span>
                      </div>
                      <p className="text-base text-gray-700">
                        Barang sudah sampai dengan selamat, terima kasih
                      </p>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
